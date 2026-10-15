"""Ask-your-record business rules (contract only, no logic yet).

No SQL, no FastAPI imports (backend.md). This module owns no tables and
persists nothing. It composes existing services: records.service for
clinical reads, analytics.service for trends and medication summaries,
audit.service for the access record, and emergency.service for the
emergency preview.

Every clinical read goes through those services, so the consent filter
(accessible_entries) applies to every answer. Ask never reads
medical_entry directly.

ONE audit event per question, carrying the intent name only. Never a
clinical value, an entity string or a note excerpt (clinical-safety.md).
A consent-denied question and a question with no data return the same
response shape, so the answer cannot reveal which of the two happened.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.actor import Actor
from app.core.authz import Role
from app.core.errors import ErrorCode
from app.core.exceptions import PulseError
from app.core.transactions import transactional
from app.modules.ask.intents import (
    SUGGESTED_INTENTS,
    AskIntent,
    IntentMatch,
    match_entity,
    match_intent,
)
from app.modules.ask.schemas import (
    AccessLogBlock,
    AskBlock,
    AskReceipt,
    AskRequest,
    AskResponse,
    ChangesBlock,
    EmergencyPreviewBlock,
    EntryItem,
    EntryListBlock,
    LabTrendBlock,
    LabValueBlock,
    MessageBlock,
    SuggestionsBlock,
)
from app.modules.audit import service as audit_service
from app.modules.audit.service import AuditAction, AuditMetadata, AuditOutcome
from app.modules.emergency import service as emergency_service
from app.modules.records import service as records_service
from app.modules.records.schemas import EntrySummary, EntryType, LabTrendPoint
from app.modules.users import service as users_service

_DEFAULT_WINDOW_DAYS = 30
_FETCH_LIMIT = 100

Answer = tuple[list[AskBlock], AskReceipt]


def _not_found() -> PulseError:
    return PulseError(ErrorCode.NOT_FOUND, "Not found.", http_status=404)


def _none(key: str, **params: str | int | float) -> Answer:
    """The one shape for "nothing to show": consent-denied and no-data are
    deliberately indistinguishable."""
    return [MessageBlock(key=key, params=params)], AskReceipt(filter="none", audit_logged=True)


def _abnormal(point: LabTrendPoint) -> bool:
    v = point.value_numeric
    if v is None:
        return False
    low, high = point.reference_low, point.reference_high
    return (low is not None and v < low) or (high is not None and v > high)


async def _lab(session: AsyncSession, actor: Actor, patient_id: UUID, match: IntentMatch) -> Answer:
    tests = await records_service.lab_tests(session, actor, patient_id)
    if not tests:
        return _none("ask.lab.no_tests")
    name = match_entity([t.display_name for t in tests], match.entity or "")
    if name is None:
        names = ", ".join(sorted({t.display_name for t in tests})[:5])
        return _none("ask.lab.unknown_test", tests=names)
    test = next(t for t in tests if t.display_name == name)
    points = await records_service.lab_trend(
        session, actor, patient_id, code_system=test.code_system, code=test.code
    )
    if not points:
        return _none("ask.lab.no_tests")
    points = sorted(points, key=lambda p: p.occurred_at)
    receipt = AskReceipt(filter="accessible_entries", entry_count=len(points))
    if match.intent is AskIntent.LAB_TREND:
        flagged = [p.model_copy(update={"is_abnormal": _abnormal(p)}) for p in points]
        unit = next((p.unit for p in reversed(points) if p.unit), None)
        return [LabTrendBlock(test_name=name, unit=unit, points=flagged)], receipt
    last = points[-1]
    block = LabValueBlock(
        test_name=name,
        value_numeric=last.value_numeric,
        value_text=last.value_text,
        unit=last.unit,
        reference_low=last.reference_low,
        reference_high=last.reference_high,
        is_abnormal=_abnormal(last),
        observed_at=last.occurred_at,
    )
    return [block], receipt


async def _medications(session: AsyncSession, actor: Actor, patient_id: UUID) -> Answer:
    meds = await records_service.active_medications(session, actor, patient_id)
    if not meds:
        return _none("ask.medications.none")
    items = [
        EntryItem(
            display_name=m.medication_name,
            detail=" · ".join(x for x in (m.dosage, m.frequency, m.route) if x) or None,
            recorded_at=m.occurred_at,
        )
        for m in meds
    ]
    block = EntryListBlock(list_kind="medications", items=items)
    return [block], AskReceipt(filter="accessible_entries", entry_count=len(items))


async def _conditions(session: AsyncSession, actor: Actor, patient_id: UUID) -> Answer:
    page = await records_service.list_timeline(
        session, actor, patient_id, entry_type=EntryType.DIAGNOSIS, limit=_FETCH_LIMIT
    )
    current = [e for e in page.items if e.superseded_by_id is None]
    if not current:
        return _none("ask.conditions.none")
    items = [
        EntryItem(entry_id=e.id, display_name=e.summary or "-", recorded_at=e.recorded_at)
        for e in current
    ]
    block = EntryListBlock(list_kind="conditions", items=items)
    return [block], AskReceipt(filter="accessible_entries", entry_ids=[e.id for e in current])


async def _allergies(session: AsyncSession, actor: Actor) -> Answer:
    # Allergies are not a Medical Entry type; they live on the Emergency Card.
    card = await emergency_service.get_own(session, actor)
    if not card.allergies:
        return _none("ask.allergies.none")
    item = EntryItem(display_name=card.allergies, recorded_at=card.updated_at or datetime.now(UTC))
    block = EntryListBlock(list_kind="allergies", items=[item])
    return [block], AskReceipt(filter="emergency_card", entry_count=1)


async def _what_changed(
    session: AsyncSession, actor: Actor, patient_id: UUID, window_days: int
) -> Answer:
    since = datetime.now(UTC) - timedelta(days=window_days)
    page = await records_service.list_timeline(session, actor, patient_id, limit=_FETCH_LIMIT)
    recent = [e for e in page.items if e.recorded_at >= since]

    def item(e: EntrySummary) -> EntryItem:
        return EntryItem(
            entry_id=e.id,
            display_name=e.summary or e.entry_type.value,
            detail=e.entry_type.value,
            recorded_at=e.recorded_at,
        )

    added = [item(e) for e in recent if e.superseded_by_id is None]
    superseded = [item(e) for e in recent if e.superseded_by_id is not None]
    if not added and not superseded:
        return _none("ask.changed.none", days=window_days)
    block = ChangesBlock(window_days=window_days, since=since, added=added, superseded=superseded)
    ids = [e.id for e in recent]
    return [block], AskReceipt(filter="accessible_entries", entry_ids=ids)


async def _who_accessed(session: AsyncSession, actor: Actor, window_days: int) -> Answer:
    since = datetime.now(UTC) - timedelta(days=window_days)
    page = await audit_service.list_for_patient(
        session, actor, None, since=since, limit=_FETCH_LIMIT
    )
    others = [e for e in page.items if not e.is_self]
    if not others:
        return _none("ask.access.none", days=window_days)
    block = AccessLogBlock(
        window_days=window_days,
        total=len(others),
        truncated=page.next_cursor is not None,
        items=others,
    )
    return [block], AskReceipt(filter="audit_projection", entry_count=len(others))


async def _emergency(session: AsyncSession, actor: Actor, patient_id: UUID) -> Answer:
    view = await emergency_service.view_for_patient(session, actor, patient_id)
    fields = view.model_dump(exclude={"patient_id", "patient_name"})
    card = view if any(fields.values()) else None
    return [EmergencyPreviewBlock(card=card)], AskReceipt(filter="emergency_card")


@transactional
async def ask(session: AsyncSession, actor: Actor, request: AskRequest) -> AskResponse:
    """A patient asks about their own record. The patient is resolved from
    the actor, never from the request, so a question cannot name another
    Patient. Anyone who is not a Patient (Administrators included, ADR-0007)
    gets 404 and no clinical blocks.
    """
    if actor.role is not Role.PATIENT:
        raise _not_found()
    patient = await users_service.get_own_patient_profile(session, actor)
    if patient is None:
        raise _not_found()

    match = match_intent(request.question, request.locale)
    days = request.window_days or match.window_days or _DEFAULT_WINDOW_DAYS
    intent = match.intent

    if intent in (AskIntent.LATEST_LAB, AskIntent.LAB_TREND):
        blocks, receipt = await _lab(session, actor, patient.id, match)
    elif intent is AskIntent.MEDICATIONS:
        blocks, receipt = await _medications(session, actor, patient.id)
    elif intent is AskIntent.CONDITIONS:
        blocks, receipt = await _conditions(session, actor, patient.id)
    elif intent is AskIntent.ALLERGIES:
        blocks, receipt = await _allergies(session, actor)
    elif intent is AskIntent.WHAT_CHANGED:
        blocks, receipt = await _what_changed(session, actor, patient.id, days)
    elif intent is AskIntent.WHO_ACCESSED:
        blocks, receipt = await _who_accessed(session, actor, days)
    elif intent is AskIntent.EMERGENCY_PREVIEW:
        blocks, receipt = await _emergency(session, actor, patient.id)
    else:
        blocks = [
            MessageBlock(key="ask.unmatched"),
            SuggestionsBlock(intents=list(SUGGESTED_INTENTS)),
        ]
        return AskResponse(
            intent=intent,
            blocks=blocks,
            receipt=AskReceipt(filter="none", audit_logged=False),
        )

    # One event per question. Intent name and row count only: never the
    # question, an entity string, or any answer content (clinical-safety.md).
    await audit_service.emit(
        session,
        actor=actor,
        action=AuditAction.ANALYTICS_VIEWED,
        resource_type="ask",
        resource_id=None,
        patient_id=patient.id,
        outcome=AuditOutcome.SUCCESS,
        metadata=AuditMetadata(intent=intent.value, count=receipt.entry_count or None),
    )
    return AskResponse(intent=intent, blocks=blocks, receipt=receipt)
