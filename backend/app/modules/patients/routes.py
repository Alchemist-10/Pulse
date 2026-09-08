"""Patients HTTP surface.

Endpoints (Wave 1, Agent A):
  GET /api/v1/patients/me       requires(PATIENT_PROFILE_READ_SELF) — real, seeded row
  GET /api/v1/patients/{id}     requires(PATIENT_PROFILE_READ_SELF) — @stub, X-Pulse-Stub: true
"""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import Permission
from app.core.errors import ErrorCode
from app.core.exceptions import PulseError
from app.core.stub import stub
from app.db.session import get_session
from app.modules.auth.dependencies import AuthContext, current_user, requires
from app.modules.patients.schemas import PatientProfile
from app.modules.users import service as users_service

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[AuthContext, Depends(current_user)]

_STUB_PROFILE = PatientProfile(
    id=UUID("00000000-0000-0000-0000-0000000000aa"),
    full_name="Ananya Iyer",
    date_of_birth=date(1990, 5, 14),
    sex="FEMALE",
    phone="+91 98840 11223",
    address_line="14 Kamaraj Salai",
    city="Chennai",
    state="Tamil Nadu",
    locale_preference="en",
    claimed=True,
)


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
    dependencies=[requires(Permission.PATIENT_PROFILE_READ_SELF)],
)
@stub(_STUB_PROFILE)
async def read_profile_by_id(
    patient_id: UUID, response: Response, ctx: CurrentUser
) -> PatientProfile:
    return _STUB_PROFILE
