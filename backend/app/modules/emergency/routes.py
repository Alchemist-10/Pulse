"""Emergency card HTTP surface. HTTP only — parse, guard, delegate."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import Permission
from app.db.session import get_session
from app.modules.auth.dependencies import AuthContext, current_user, requires, throttled
from app.modules.emergency import service
from app.modules.emergency.schemas import (
    EmergencyCard,
    EmergencyCardUpdate,
    EmergencyCardView,
)

router = APIRouter(prefix="/api/v1", tags=["emergency"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[AuthContext, Depends(current_user)]


@router.get("/emergency-card", dependencies=[requires(Permission.EMERGENCY_CARD_MANAGE_SELF)])
async def get_own_card(ctx: CurrentUser, session: SessionDep) -> EmergencyCard:
    return await service.get_own(session, ctx.actor)


@router.put("/emergency-card", dependencies=[requires(Permission.EMERGENCY_CARD_MANAGE_SELF)])
async def update_own_card(
    payload: EmergencyCardUpdate, ctx: CurrentUser, session: SessionDep
) -> EmergencyCard:
    return await service.update_own(session, ctx.actor, payload)


@router.post("/emergency-card/qr", dependencies=[requires(Permission.EMERGENCY_CARD_MANAGE_SELF)])
async def rotate_qr(ctx: CurrentUser, session: SessionDep) -> EmergencyCard:
    return await service.rotate_qr(session, ctx.actor)


@router.delete("/emergency-card/qr", dependencies=[requires(Permission.EMERGENCY_CARD_MANAGE_SELF)])
async def disable_qr(ctx: CurrentUser, session: SessionDep) -> EmergencyCard:
    return await service.disable_qr(session, ctx.actor)


@router.get(
    "/emergency-card/by-token/{token}",
    dependencies=[requires(Permission.EMERGENCY_CARD_VIEW), throttled("emergency-scan", limit=30)],
)
async def view_by_token(token: str, ctx: CurrentUser, session: SessionDep) -> EmergencyCardView:
    return await service.view_by_token(session, ctx.actor, token)


@router.get(
    "/patients/{patient_id}/emergency-card",
    dependencies=[requires(Permission.EMERGENCY_CARD_VIEW)],
)
async def view_patient_card(
    patient_id: UUID, ctx: CurrentUser, session: SessionDep
) -> EmergencyCardView:
    return await service.view_for_patient(session, ctx.actor, patient_id)
