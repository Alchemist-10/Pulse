"""Ask-your-record HTTP surface. HTTP only: parse, guard, delegate.

`RECORDS_READ` is the same permission every clinical read uses and no
Administrator holds it (ADR-0007); `service.ask` additionally 404s any
non-Patient actor.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import Permission
from app.db.session import get_session
from app.modules.ask import service
from app.modules.ask.schemas import AskRequest, AskResponse
from app.modules.auth.dependencies import AuthContext, current_user, requires

router = APIRouter(prefix="/api/v1/ask", tags=["ask"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[AuthContext, Depends(current_user)]


@router.post("", dependencies=[requires(Permission.RECORDS_READ)])
async def post_ask(body: AskRequest, ctx: CurrentUser, session: SessionDep) -> AskResponse:
    return await service.ask(session, ctx.actor, body)
