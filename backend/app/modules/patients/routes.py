"""Patients HTTP surface.

Endpoints:
  GET /api/v1/patients/me     requires(PATIENT_PROFILE_READ_SELF) — the signed-in
                              Patient's own row
  GET /api/v1/patients/{id}   requires(RECORDS_READ) — same row, resolved through
                              the same access rules as the clinical read (the G2
                              stub this replaced was the last in the inventory)
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import Permission
from app.core.errors import ErrorCode
from app.core.exceptions import PulseError
from app.db.session import get_session
from app.modules.auth.dependencies import AuthContext, current_user, requires
from app.modules.patients.schemas import PatientProfile
from app.modules.users import service as users_service

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[AuthContext, Depends(current_user)]


@router.get(
    "/me",
    dependencies=[requires(Permission.PATIENT_PROFILE_READ_SELF)],
)
async def read_own_profile(ctx: CurrentUser, session: SessionDep) -> PatientProfile:
    profile = await users_service.get_own_patient_profile(session, ctx.actor)
    if profile is None:
        raise PulseError(
            ErrorCode.NOT_FOUND,
            "No patient profile exists for this account.",
            http_status=status.HTTP_404_NOT_FOUND,
        )
    return profile


@router.get(
    "/{patient_id}",
    dependencies=[requires(Permission.RECORDS_READ)],
)
async def read_profile_by_id(
    patient_id: UUID, ctx: CurrentUser, session: SessionDep
) -> PatientProfile:
    """One Patient's identity profile. Guarded by `RECORDS_READ` — not
    `PATIENT_PROFILE_READ_SELF` — so a Clinician reaches the consent-aware
    resolution and is denied with 404 by `users_service`
    .get_patient_profile_for_actor`, never a 403 that would confirm the
    Patient exists (clinical-safety.md); identical shape to the timeline
    endpoint's guard. An Administrator is stopped right here by the guard
    (ADR-0007), and would resolve no access even if they weren't."""
    profile = await users_service.get_patient_profile_for_actor(session, ctx.actor, patient_id)
    if profile is None:
        raise PulseError(
            ErrorCode.NOT_FOUND,
            "No patient profile exists for this account.",
            http_status=status.HTTP_404_NOT_FOUND,
        )
    return profile
