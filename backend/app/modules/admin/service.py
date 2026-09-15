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

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.actor import Actor
from app.modules.admin.schemas import (
    AdminPatientIdentity,
    DuplicateReviewCandidate,
    MergeRecord,
    MergeResult,
)
from app.modules.records import service as records_service
from app.modules.users import service as users_service

# `users.models.Patient` — typed as `Any` rather than imported: this module
# talks to `users` only through `users.service` (backend.md), and the
# cross-module import lint (`scripts/lint_cross_module_imports.py`) bars
# reaching into another module's `models` even for a type hint.
_Patient = Any


async def _identity(session: AsyncSession, actor: Actor, patient: _Patient) -> AdminPatientIdentity:
    count = await records_service.entry_count_for_patient(session, actor, patient.id)
    return AdminPatientIdentity(
        id=patient.id,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth,
        phone=patient.phone,
        claimed=patient.user_id is not None,
        entry_count=count,
    )


async def duplicate_review_queue(
    session: AsyncSession, actor: Actor
) -> list[DuplicateReviewCandidate]:
    """Identity fields + entry counts only, never entry content (ADR-0007,
    ADR-0011). `list_duplicate_review_queue` gates to Administrator."""
    items = await users_service.list_duplicate_review_queue(session, actor)
    candidates: list[DuplicateReviewCandidate] = []
    for item in items:
        patient_a = await users_service.get_patient(session, item.patient_id_a)
        patient_b = await users_service.get_patient(session, item.patient_id_b)
        if patient_a is None or patient_b is None:  # pragma: no cover - defensive
            continue
        candidates.append(
            DuplicateReviewCandidate(
                id=item.id,
                patient_a=await _identity(session, actor, patient_a),
                patient_b=await _identity(session, actor, patient_b),
                score=float(item.score),
                # `DuplicateReviewItem.status` maps to a plain `String`
                # column (not `SAEnum`), so the value read back off a real
                # row is already the raw string `ReviewStatus` value.
                status=str(item.status),
            )
        )
    return candidates


async def mark_not_duplicate(
    session: AsyncSession, actor: Actor, patient_id_a: UUID, patient_id_b: UUID
) -> None:
    await users_service.mark_not_duplicate(session, actor, patient_id_a, patient_id_b)


def _to_merge_result(merge: object) -> MergeResult:
    return MergeResult(
        id=merge.id,  # type: ignore[attr-defined]
        winner_patient_id=merge.winner_patient_id,  # type: ignore[attr-defined]
        loser_patient_id=merge.loser_patient_id,  # type: ignore[attr-defined]
        occurred_at=merge.occurred_at,  # type: ignore[attr-defined]
        reversed_at=merge.reversed_at,  # type: ignore[attr-defined]
    )


async def merge(
    session: AsyncSession, actor: Actor, winner_patient_id: UUID, loser_patient_id: UUID
) -> MergeResult:
    """Human-admin-only, reversible (ADR-0011). `merge_patients` gates to
    Administrator and rejects any other caller, including a background job."""
    result = await users_service.merge_patients(
        session, actor, winner_patient_id, loser_patient_id
    )
    return _to_merge_result(result)


async def reversible_merges(session: AsyncSession, actor: Actor) -> list[MergeRecord]:
    """`list_reversible_merges` gates to Administrator."""
    records: list[MergeRecord] = []
    for merge in await users_service.list_reversible_merges(session, actor):
        winner = await users_service.get_patient(session, merge.winner_patient_id)
        loser = await users_service.get_patient(session, merge.loser_patient_id)
        if winner is None or loser is None:  # pragma: no cover - FK-guaranteed
            continue
        records.append(
            MergeRecord(
                **_to_merge_result(merge).model_dump(),
                winner_name=winner.full_name,
                loser_name=loser.full_name,
            )
        )
    return records


async def reverse(session: AsyncSession, actor: Actor, merge_id: UUID) -> MergeResult:
    result = await users_service.reverse_merge(session, actor, merge_id)
    return _to_merge_result(result)
