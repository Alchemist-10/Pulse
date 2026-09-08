"""Records repository — all SQL for Medical Entries and Documents.

G1 contract (P2.2, #27): signatures merge first raising
`NotImplementedError`; implementations land in P2.3 (timeline), P2.5
(records service), P2.6 (documents) and P2.7 (correction). Services call
these; they never build queries.

`accessible_entries` (ADR-0006) is the one query builder every clinical
read composes from; it stays a signature until Phase 3 fills in the five
access rules. Every entry-returning function here takes an `actor` — if a
signature has no actor, the access rules have nowhere to apply
(clinical-safety.md).
"""

from typing import Any
from uuid import UUID

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.actor import Actor
from app.core.pagination import Page
from app.modules.records.models import EntryType, MedicalDocument, MedicalEntry
from app.modules.records.schemas import DocumentCreate, EntryCreate


async def accessible_entries(
    session: AsyncSession, actor: Actor, patient_id: UUID
) -> Select[Any]:
    """The subset of a Patient's Medical Entries `actor` may read.

    Composable filter, not a result set. Implemented in Phase 3.
    """
    raise NotImplementedError


async def list_timeline(
    session: AsyncSession,
    actor: Actor,
    patient_id: UUID,
    *,
    entry_type: EntryType | None = None,
    cursor: str | None = None,
    limit: int = 50,
) -> Page[MedicalEntry]:
    """Cursor-paginated, `occurred_at DESC`, `superseded_by_id IS NULL`,
    polymorphic via `selectin_polymorphic`. Composes from
    `accessible_entries`. Implemented in P2.3."""
    raise NotImplementedError


async def get_entry(
    session: AsyncSession, actor: Actor, entry_id: UUID
) -> MedicalEntry | None:
    """One entry, subtype loaded, reachable even when superseded. Composes
    from `accessible_entries`. Implemented in P2.5."""
    raise NotImplementedError


async def insert_entry(
    session: AsyncSession, actor: Actor, patient_id: UUID, payload: EntryCreate
) -> MedicalEntry:
    """Insert a trunk row plus its subtype row. Never updates in place.
    Implemented in P2.5."""
    raise NotImplementedError


async def supersede_entry(
    session: AsyncSession,
    actor: Actor,
    patient_id: UUID,
    original_id: UUID,
    replacement_payload: EntryCreate,
) -> MedicalEntry:
    """Insert the replacement, stamp `superseded_by_id` on the original.
    The one permitted UPDATE on a clinical row. Implemented in P2.7."""
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
