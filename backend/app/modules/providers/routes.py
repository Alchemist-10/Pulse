"""Providers HTTP surface (P2.5)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import Permission
from app.db.session import get_session
from app.modules.auth.dependencies import AuthContext, current_user, requires
from app.modules.providers import service
from app.modules.providers.schemas import Provider

router = APIRouter(prefix="/api/v1/providers", tags=["providers"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[AuthContext, Depends(current_user)]


@router.get("/{provider_id}", dependencies=[requires(Permission.PROVIDER_READ)])
async def get_provider(
    provider_id: UUID, ctx: CurrentUser, session: SessionDep
) -> Provider:
    return await service.get_provider(session, ctx.actor, provider_id)
