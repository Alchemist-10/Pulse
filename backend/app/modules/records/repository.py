"""Records repository.

Phase 1 contributes only the signature of `accessible_entries` — the one
query builder every clinical read composes from (ADR-0006). It raises
until Phase 3 fills in the five access rules. Its existence now gives the
`select(MedicalEntry)` lint and the actor-first convention a target.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.actor import Actor


async def accessible_entries(
    session: AsyncSession, actor: Actor, patient_id: UUID
) -> Select[Any]:
    """The subset of a Patient's Medical Entries `actor` may read.

    Composable filter, not a result set. Implemented in Phase 3.
    """
    raise NotImplementedError
