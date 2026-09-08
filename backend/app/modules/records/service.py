"""Records business rules (P2.5).

No SQL, no FastAPI imports (backend.md). Every entry-returning function
takes an `Actor`; there are no "internal" helpers that skip it — the pure
ORM->wire mappers live in `projections.py` precisely so they are not
somewhere a filter could have been dropped.

Phase 2 access is rule 1 only — a Patient reads their own history. A
non-owner (Clinician, Administrator, another Patient) gets **404, never
403**: a 403 would confirm the record exists (clinical-safety.md). Rules
2–4 (Clinician consent, break-glass) land in Phase 3, and the read paths
below carry `# TODO(P3): emit ENTRY_VIEWED` — no audit rows this phase.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.actor import Actor
from app.core.errors import ErrorCode
from app.core.exceptions import PulseError
from app.core.pagination import Page
from app.modules.records import projections, repository
from app.modules.records.models import EntryType
from app.modules.records.schemas import EntryCreate, EntryDetail, EntrySummary
from app.modules.users import service as users_service

_REQUIRED_FIELDS: dict[EntryType, tuple[str, ...]] = {
    EntryType.DIAGNOSIS: ("code_system", "code", "display_name"),
    EntryType.PROCEDURE: ("code_system", "code", "display_name"),
    EntryType.LAB_REPORT: ("code_system", "code", "display_name"),
    EntryType.PRESCRIPTION: ("medication_name",),
    EntryType.CLINICAL_NOTE: ("text",),
}


def _not_found() -> PulseError:
    return PulseError(ErrorCode.NOT_FOUND, "No such record.", http_status=404)


async def _require_owned_patient(
    session: AsyncSession, actor: Actor, patient_id: UUID
) -> None:
    patient = await users_service.get_patient(session, patient_id)
    if patient is None or patient.user_id != actor.user_id:
        raise _not_found()


def _validate_payload(payload: EntryCreate) -> None:
    missing = [
        field
        for field in _REQUIRED_FIELDS[payload.entry_type]
        if not getattr(payload, field, None)
    ]
    if missing:
        raise PulseError(
            ErrorCode.ENTRY_TYPE_MISMATCH,
            f"{payload.entry_type.value} requires {', '.join(missing)}.",
            http_status=422,
        )


async def list_timeline(
    session: AsyncSession,
    actor: Actor,
    patient_id: UUID,
    *,
    entry_type: EntryType | None = None,
    cursor: str | None = None,
    limit: int = 50,
) -> Page[EntrySummary]:
    await _require_owned_patient(session, actor, patient_id)
    rows, next_cursor = await repository.list_timeline(
        session, actor, patient_id, entry_type=entry_type, cursor=cursor, limit=limit
    )
    # TODO(P3): emit ENTRY_VIEWED
    return Page[EntrySummary](
        items=[projections.to_summary(r) for r in rows], next_cursor=next_cursor
    )


async def get_entry(session: AsyncSession, actor: Actor, entry_id: UUID) -> EntryDetail:
    entry = await repository.get_entry(session, actor, entry_id)
    if entry is None:
        raise _not_found()
    await _require_owned_patient(session, actor, entry.patient_id)
    supersedes_id = await repository.get_superseding_original_id(session, entry_id)
    documents = await repository.list_documents(session, entry_id)
    # TODO(P3): emit ENTRY_VIEWED
    return projections.to_detail(
        entry, supersedes_id=supersedes_id, documents=documents
    )


async def insert_entry(
    session: AsyncSession, actor: Actor, patient_id: UUID, payload: EntryCreate
) -> EntryDetail:
    """File a new Entry for a Patient. The route restricts this to Provider
    Staff (RECORDS_WRITE)."""
    patient = await users_service.get_patient(session, patient_id)
    if patient is None:
        raise _not_found()
    _validate_payload(payload)
    if payload.source_provider_id is None:
        provider_id = await users_service.get_provider_for_staff(
            session, actor.user_id
        )
        payload = payload.model_copy(update={"source_provider_id": provider_id})
    entry = await repository.insert_entry(session, actor, patient_id, payload)
    await session.commit()
    fresh = await repository.get_entry(session, actor, entry.id)
    if fresh is None:  # pragma: no cover - just inserted
        raise _not_found()
    return projections.to_detail(fresh, supersedes_id=None, documents=[])


async def supersede_entry(
    session: AsyncSession,
    actor: Actor,
    patient_id: UUID,
    original_id: UUID,
    payload: EntryCreate,
) -> EntryDetail:
    """Correction path — insert a replacement, stamp `superseded_by_id` on
    the original. Implemented in P2.7."""
    raise NotImplementedError
