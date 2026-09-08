"""Records repository — all SQL for Medical Entries and Documents.

`accessible_entries` (ADR-0006) is the one query builder every clinical
read composes from. Phase 2 implements **rule 1 only** — a Patient's own
history; rules 2–4 (Clinician consent, break-glass) raise until Phase 3.
Every entry-returning function takes an `actor`: if a signature has no
actor, the access rules have nowhere to apply (clinical-safety.md).

`list_timeline` / `get_entry` land here in P2.3 / P2.5; `insert_entry` in
P2.5; `supersede_entry` in P2.7; the document functions in P2.6.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectin_polymorphic

from app.core.actor import Actor
from app.core.pagination import decode_cursor, encode_cursor
from app.modules.records.models import (
    ClinicalNote,
    Diagnosis,
    EntryType,
    LabReport,
    MedicalDocument,
    MedicalEntry,
    Prescription,
    Procedure,
)
from app.modules.records.schemas import DocumentCreate, EntryCreate

_SUBTYPES = (Diagnosis, Prescription, LabReport, Procedure, ClinicalNote)
_MAX_LIMIT = 100


async def accessible_entries(
    session: AsyncSession, actor: Actor, patient_id: UUID
) -> Select[Any]:
    """The subset of a Patient's Medical Entries `actor` may read.

    Composable filter, not a result set. Phase 2: rule 1 — the Patient's
    own history. The caller (service) has already established that `actor`
    owns `patient_id`; rules 2–4 arrive in Phase 3.
    """
    return select(MedicalEntry).where(MedicalEntry.patient_id == patient_id)


def _pack_cursor(occurred_at: datetime, entry_id: UUID) -> str:
    return encode_cursor(f"{occurred_at.isoformat()}|{entry_id}")


def _unpack_cursor(cursor: str) -> tuple[datetime, UUID]:
    raw = decode_cursor(cursor)
    ts, _, uid = raw.partition("|")
    return datetime.fromisoformat(ts), UUID(uid)


async def list_timeline(
    session: AsyncSession,
    actor: Actor,
    patient_id: UUID,
    *,
    entry_type: EntryType | None = None,
    cursor: str | None = None,
    limit: int = 50,
) -> tuple[list[MedicalEntry], str | None]:
    """`occurred_at DESC`, `superseded_by_id IS NULL`, polymorphic via
    `selectin_polymorphic` (also the async `MissingGreenlet` fix). Opaque
    keyset cursor over `(occurred_at, id)` — never offset."""
    limit = max(1, min(limit, _MAX_LIMIT))
    stmt = (await accessible_entries(session, actor, patient_id)).where(
        MedicalEntry.superseded_by_id.is_(None)
    )
    if entry_type is not None:
        stmt = stmt.where(MedicalEntry.entry_type == entry_type)
    if cursor is not None:
        c_at, c_id = _unpack_cursor(cursor)
        stmt = stmt.where(
            or_(
                MedicalEntry.occurred_at < c_at,
                (MedicalEntry.occurred_at == c_at) & (MedicalEntry.id < c_id),
            )
        )
    stmt = (
        stmt.order_by(MedicalEntry.occurred_at.desc(), MedicalEntry.id.desc())
        .options(selectin_polymorphic(MedicalEntry, list(_SUBTYPES)))
        .limit(limit + 1)
    )
    rows = list((await session.execute(stmt)).scalars().all())
    next_cursor: str | None = None
    if len(rows) > limit:
        rows = rows[:limit]
        tail = rows[-1]
        next_cursor = _pack_cursor(tail.occurred_at, tail.id)
    return rows, next_cursor


async def get_entry(
    session: AsyncSession, actor: Actor, entry_id: UUID
) -> MedicalEntry | None:
    """One entry by id, subtype loaded, reachable even when superseded.

    Phase 2 gate (actor owns the patient) is applied by the service; the
    filter moves into `accessible_entries` in Phase 3.
    """
    stmt = (
        select(MedicalEntry)
        .where(MedicalEntry.id == entry_id)
        .options(selectin_polymorphic(MedicalEntry, list(_SUBTYPES)))
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_superseding_original_id(
    session: AsyncSession, entry_id: UUID
) -> UUID | None:
    """The id of the Entry that `entry_id` supersedes, if any (reverse of
    `superseded_by_id`). Non-clinical, no actor needed."""
    stmt = select(MedicalEntry.id).where(MedicalEntry.superseded_by_id == entry_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def list_documents(
    session: AsyncSession, entry_id: UUID
) -> list[MedicalDocument]:
    """Document metadata for one Entry. Access is gated on the Entry by the
    caller; this is a plain child fetch."""
    stmt = select(MedicalDocument).where(MedicalDocument.entry_id == entry_id)
    return list((await session.execute(stmt)).scalars().all())


def _subtype_kwargs(entry_type: EntryType, payload: EntryCreate) -> dict[str, Any]:
    if entry_type in (EntryType.DIAGNOSIS, EntryType.PROCEDURE):
        return {
            "code_system": payload.code_system,
            "code": payload.code,
            "display_name": payload.display_name,
        }
    if entry_type is EntryType.LAB_REPORT:
        return {
            "code_system": payload.code_system,
            "code": payload.code,
            "display_name": payload.display_name,
            "value_numeric": payload.value_numeric,
            "value_text": payload.value_text,
            "unit": payload.unit,
            "reference_low": payload.reference_low,
            "reference_high": payload.reference_high,
        }
    if entry_type is EntryType.PRESCRIPTION:
        return {
            "medication_name": payload.medication_name,
            "code_system": payload.code_system,
            "code": payload.code,
            "display_name": payload.display_name,
            "dosage": payload.dosage,
            "frequency": payload.frequency,
            "route": payload.route,
        }
    return {"text": payload.text}


_SUBTYPE_CLASS: dict[EntryType, type[MedicalEntry]] = {
    EntryType.DIAGNOSIS: Diagnosis,
    EntryType.PROCEDURE: Procedure,
    EntryType.LAB_REPORT: LabReport,
    EntryType.PRESCRIPTION: Prescription,
    EntryType.CLINICAL_NOTE: ClinicalNote,
}


async def insert_entry(
    session: AsyncSession, actor: Actor, patient_id: UUID, payload: EntryCreate
) -> MedicalEntry:
    """Insert a trunk row plus its subtype row in one flush. Never updates
    in place. `author_user_id` is the acting user."""
    cls = _SUBTYPE_CLASS[payload.entry_type]
    entry = cls(
        patient_id=patient_id,
        entry_type=payload.entry_type,
        occurred_at=payload.occurred_at,
        is_critical=payload.is_critical,
        source_provider_id=payload.source_provider_id,
        author_user_id=actor.user_id,
        entry_metadata=payload.metadata or {},
        **_subtype_kwargs(payload.entry_type, payload),
    )
    session.add(entry)
    await session.flush()
    return entry


async def supersede_entry(
    session: AsyncSession,
    actor: Actor,
    patient_id: UUID,
    original_id: UUID,
    replacement_payload: EntryCreate,
) -> MedicalEntry:
    """Insert the replacement, stamp `superseded_by_id` on the original.
    Implemented in P2.7."""
    raise NotImplementedError


async def add_document(
    session: AsyncSession, actor: Actor, entry_id: UUID, meta: DocumentCreate
) -> MedicalDocument:
    """Record metadata for a file already stored behind the
    StorageProvider. Implemented in P2.6."""
    raise NotImplementedError


async def get_document(
    session: AsyncSession, actor: Actor, document_id: UUID
) -> MedicalDocument | None:
    """Document metadata, gated by the same access rule as its Entry.
    Implemented in P2.6."""
    raise NotImplementedError
