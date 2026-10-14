"""Admin business rules (P4.3, #54).

No SQL, no FastAPI imports (backend.md). This module owns no tables of
its own — it composes `users.service` (duplicate review + merge/reversal,
P4.1/#52) and `records.service` (entry counts only, never content) through
their service interfaces, never their tables (backend.md, "modules
communicate through service interfaces").

Every function here is Administrator-only. The actual gate lives in the
functions being wrapped (`users.service._require_administrator`,
`records.service.entry_count_for_patient`) so there is exactly one place
each rule is enforced — this module never re-implements the check, it
just never calls anything that would let a non-Administrator through.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.actor import Actor
from app.core.authz import Role
from app.core.errors import ErrorCode
from app.core.exceptions import PulseError
from app.core.pagination import Page
from app.modules.admin.schemas import (
    AdminPatientDetail,
    AdminPatientIdentity,
    AdminPatientRow,
    AdminSummary,
    AdminUserRow,
    DuplicateReviewCandidate,
    MergeRecord,
    MergeResult,
)
from app.modules.audit import service as audit_service
from app.modules.consent import service as consent_service
from app.modules.records import service as records_service
from app.modules.users import service as users_service


class _Patient(Protocol):
    id: UUID
    full_name: str
    date_of_birth: date | None
    phone: str | None
    user_id: UUID | None


class _Merge(Protocol):
    id: UUID
    winner_patient_id: UUID
    loser_patient_id: UUID
    occurred_at: datetime
    reversed_at: datetime | None


def _identity(patient: _Patient, count: int) -> AdminPatientIdentity:
    return AdminPatientIdentity(
        id=patient.id,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth,
        phone=patient.phone,
        claimed=patient.user_id is not None,
        entry_count=count,
    )


async def duplicate_review_queue(
    session: AsyncSession, actor: Actor, *, cursor: str | None = None, limit: int = 50
) -> Page[DuplicateReviewCandidate]:
    """Identity fields + entry counts only, never entry content (ADR-0007,
    ADR-0011). `list_duplicate_review_queue` gates to Administrator."""
    items, next_cursor = await users_service.duplicate_review_page(
        session, actor, cursor=cursor, limit=limit
    )
    candidates: list[DuplicateReviewCandidate] = []
    patient_ids = list({pid for item in items for pid in (item.patient_id_a, item.patient_id_b)})
    patients = await users_service.patient_map(session, patient_ids)
    counts = await records_service.entry_counts_for_patients(session, actor, patient_ids)
    for item in items:
        patient_a = patients.get(item.patient_id_a)
        patient_b = patients.get(item.patient_id_b)
        if patient_a is None or patient_b is None:  # pragma: no cover - defensive
            continue
        candidates.append(
            DuplicateReviewCandidate(
                id=item.id,
                patient_a=_identity(patient_a, counts.get(patient_a.id, 0)),
                patient_b=_identity(patient_b, counts.get(patient_b.id, 0)),
                score=float(item.score),
                # `DuplicateReviewItem.status` maps to a plain `String`
                # column (not `SAEnum`), so the value read back off a real
                # row is already the raw string `ReviewStatus` value.
                status=str(item.status),
            )
        )
    return Page[DuplicateReviewCandidate](items=candidates, next_cursor=next_cursor)


async def mark_not_duplicate(
    session: AsyncSession, actor: Actor, patient_id_a: UUID, patient_id_b: UUID
) -> None:
    await users_service.mark_not_duplicate(session, actor, patient_id_a, patient_id_b)


def _to_merge_result(merge: _Merge) -> MergeResult:
    return MergeResult(
        id=merge.id,
        winner_patient_id=merge.winner_patient_id,
        loser_patient_id=merge.loser_patient_id,
        occurred_at=merge.occurred_at,
        reversed_at=merge.reversed_at,
    )


async def merge(
    session: AsyncSession, actor: Actor, winner_patient_id: UUID, loser_patient_id: UUID
) -> MergeResult:
    """Human-admin-only, reversible (ADR-0011). `merge_patients` gates to
    Administrator and rejects any other caller, including a background job."""
    result = await users_service.merge_patients(session, actor, winner_patient_id, loser_patient_id)
    return _to_merge_result(result)


async def reversible_merges(
    session: AsyncSession, actor: Actor, *, cursor: str | None = None, limit: int = 50
) -> Page[MergeRecord]:
    """`list_reversible_merges` gates to Administrator."""
    records: list[MergeRecord] = []
    merges, next_cursor = await users_service.reversible_merge_page(
        session, actor, cursor=cursor, limit=limit
    )
    patient_ids = list(
        {pid for merge in merges for pid in (merge.winner_patient_id, merge.loser_patient_id)}
    )
    patients = await users_service.patient_map(session, patient_ids)
    for merge in merges:
        winner = patients.get(merge.winner_patient_id)
        loser = patients.get(merge.loser_patient_id)
        if winner is None or loser is None:  # pragma: no cover - FK-guaranteed
            continue
        records.append(
            MergeRecord(
                **_to_merge_result(merge).model_dump(),
                winner_name=winner.full_name,
                loser_name=loser.full_name,
            )
        )
    return Page[MergeRecord](items=records, next_cursor=next_cursor)


async def reverse(session: AsyncSession, actor: Actor, merge_id: UUID) -> MergeResult:
    result = await users_service.reverse_merge(session, actor, merge_id)
    return _to_merge_result(result)


class _PatientFull(_Patient, Protocol):
    @property
    def sex(self) -> object | None: ...

    city: str | None
    state: str | None
    address_line: str | None
    locale_preference: str
    created_at: datetime


def _sex(patient: _PatientFull) -> str | None:
    return str(getattr(patient.sex, "value", patient.sex)) if patient.sex is not None else None


async def patient_table(
    session: AsyncSession,
    actor: Actor,
    *,
    q: str | None,
    cursor: str | None,
    limit: int,
) -> Page[AdminPatientRow]:
    rows, next_cursor = await users_service.admin_patient_page(
        session, actor, q=q, cursor=cursor, limit=limit
    )
    counts = await records_service.entry_counts_for_patients(
        session, actor, [row.id for row in rows]
    )
    items = [
        AdminPatientRow(
            **_identity(row, counts.get(row.id, 0)).model_dump(by_alias=False),
            sex=_sex(row),
            city=row.city,
            state=row.state,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return Page[AdminPatientRow](items=items, next_cursor=next_cursor)


async def patient_detail(
    session: AsyncSession, actor: Actor, patient_id: UUID
) -> AdminPatientDetail:
    patient = await users_service.admin_patient_detail(session, actor, patient_id)
    if patient is None:
        raise PulseError(ErrorCode.NOT_FOUND, "No such patient.", http_status=404)
    counts = await records_service.entry_counts_for_patients(session, actor, [patient.id])
    active, total = await consent_service.consent_counts_for_patient(session, actor, patient.id)
    events = await audit_service.count_events_for_patient(session, actor, patient.id)
    return AdminPatientDetail(
        **_identity(patient, counts.get(patient.id, 0)).model_dump(by_alias=False),
        sex=_sex(patient),
        city=patient.city,
        state=patient.state,
        created_at=patient.created_at,
        address_line=patient.address_line,
        locale_preference=patient.locale_preference,
        active_consent_count=active,
        total_consent_count=total,
        audit_event_count=events,
    )


async def user_table(
    session: AsyncSession,
    actor: Actor,
    *,
    q: str | None,
    role: Role | None,
    cursor: str | None,
    limit: int,
) -> Page[AdminUserRow]:
    rows, next_cursor = await users_service.admin_user_page(
        session, actor, q=q, role=role, cursor=cursor, limit=limit
    )
    items = [
        AdminUserRow(
            id=row.id,
            email=row.email,
            role=row.role.value,
            email_verified=row.email_verified_at is not None,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return Page[AdminUserRow](items=items, next_cursor=next_cursor)


async def summary(session: AsyncSession, actor: Actor) -> AdminSummary:
    return AdminSummary(**await users_service.admin_summary(session, actor))
