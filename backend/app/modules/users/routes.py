"""Users HTTP surface.

Endpoints:
  PUT /api/v1/users/me/locale   requires(PATIENT_PROFILE_UPDATE_SELF) — persist
                                the signed-in Patient's interface locale
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import Permission
from app.db.session import get_session
from app.modules.auth.dependencies import AuthContext, current_user, requires
from app.modules.users import service
from app.modules.users.schemas import LocalePreferenceUpdate

router = APIRouter(prefix="/api/v1/users", tags=["users"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[AuthContext, Depends(current_user)]


@router.put(
    "/me/locale",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[requires(Permission.PATIENT_PROFILE_UPDATE_SELF)],
)
async def update_own_locale(
    body: LocalePreferenceUpdate, ctx: CurrentUser, session: SessionDep
) -> None:
    await service.set_locale_preference(session, ctx.actor, body.locale)
