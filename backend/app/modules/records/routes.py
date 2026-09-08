"""Records HTTP surface (P2.5).

HTTP only — parse, guard, delegate to `service`. Consent-denied and
not-your-record reads surface from the service as 404, never 403.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import Permission
from app.core.pagination import Page
from app.db.session import get_session
from app.modules.auth.dependencies import AuthContext, current_user, requires
from app.modules.records import service
from app.modules.records.models import EntryType
from app.modules.records.schemas import EntryCreate, EntryDetail, EntrySummary

router = APIRouter(prefix="/api/v1", tags=["records"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[AuthContext, Depends(current_user)]


@router.get(
    "/patients/{patient_id}/entries",
    dependencies=[requires(Permission.RECORDS_READ)],
)
async def list_patient_entries(
    patient_id: UUID,
    ctx: CurrentUser,
    session: SessionDep,
    entry_type: Annotated[EntryType | None, Query(alias="entryType")] = None,
    cursor: str | None = None,
    limit: int = 50,
) -> Page[EntrySummary]:
    return await service.list_timeline(
        session,
        ctx.actor,
        patient_id,
        entry_type=entry_type,
        cursor=cursor,
        limit=limit,
    )


@router.get(
    "/entries/{entry_id}",
    dependencies=[requires(Permission.RECORDS_READ)],
)
async def get_entry_detail(
    entry_id: UUID, ctx: CurrentUser, session: SessionDep
) -> EntryDetail:
    return await service.get_entry(session, ctx.actor, entry_id)


@router.post(
    "/patients/{patient_id}/entries",
    status_code=status.HTTP_201_CREATED,
    dependencies=[requires(Permission.RECORDS_WRITE)],
)
async def file_entry(
    patient_id: UUID,
    payload: EntryCreate,
    ctx: CurrentUser,
    session: SessionDep,
) -> EntryDetail:
    return await service.insert_entry(session, ctx.actor, patient_id, payload)
