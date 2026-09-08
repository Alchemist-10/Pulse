"""Auth HTTP surface. HTTP only — parse, validate, delegate to service.

Endpoints (Wave 1, Agent A):
  POST /api/v1/auth/register         public
  POST /api/v1/auth/verify/resend    public
  POST /api/v1/auth/verify           public
  POST /api/v1/auth/login            public
  POST /api/v1/auth/logout           requires(USER_CREDENTIALS_CHANGE) — any authed user
  POST /api/v1/auth/logout-all       requires(USER_CREDENTIALS_CHANGE)
  POST /api/v1/auth/step-up          requires(USER_CREDENTIALS_CHANGE)
  GET  /api/v1/auth/me               requires(USER_CREDENTIALS_CHANGE)

Every route declares `public()` or `requires(...)` in its `dependencies=`.
"""

from typing import Annotated, cast

from fastapi import APIRouter, Depends, Response, status
from fastapi import params as fastapi_params
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.identity import IdentityProvider
from app.core.authz import Permission
from app.core.redis import get_redis
from app.core.sessions import SESSION_IDLE_TTL
from app.db.session import get_session
from app.modules.auth import service
from app.modules.auth.dependencies import (
    SESSION_COOKIE,
    AuthContext,
    current_user,
    get_identity_provider,
    public,
    requires,
)
from app.modules.auth.schemas import (
    LoginRequest,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    StepUpRequest,
    VerifyRequest,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _marker(dep: object) -> fastapi_params.Depends:
    """Wave 0 types `requires(...)` / `public()` as `object`; they return `Depends`."""
    return cast(fastapi_params.Depends, dep)


SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]
IdpDep = Annotated[IdentityProvider, Depends(get_identity_provider)]
CurrentUser = Annotated[AuthContext, Depends(current_user)]


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=int(SESSION_IDLE_TTL.total_seconds()),
        path="/",
        httponly=True,
        samesite="lax",
        secure=False,
    )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    dependencies=[_marker(public())],
)
async def register(
    body: RegisterRequest, session: SessionDep, idp: IdpDep
) -> RegisterResponse:
    user_id = await service.register(
        session,
        idp,
        email=body.email,
        password=body.password,
        role=body.role.value,
        locale="en",
    )
    return RegisterResponse(user_id=user_id)


@router.post(
    "/verify/resend",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[_marker(public())],
)
async def resend_verification(
    body: ResendVerificationRequest, session: SessionDep, idp: IdpDep
) -> dict[str, str]:
    await service.resend_verification(
        session, idp, email=body.email, locale="en"
    )
    return {}


@router.post("/verify", dependencies=[_marker(public())])
async def verify(
    body: VerifyRequest, session: SessionDep, idp: IdpDep
) -> dict[str, str]:
    await service.complete_verification(
        session, idp, challenge_id=body.challenge_id, token=body.token
    )
    return {}


@router.post("/login", dependencies=[_marker(public())])
async def login(
    body: LoginRequest, response: Response, session: SessionDep, redis: RedisDep
) -> dict[str, str]:
    token = await service.login(
        session, redis, email=body.email, password=body.password
    )
    _set_session_cookie(response, token)
    return {}


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[_marker(requires(Permission.USER_CREDENTIALS_CHANGE))],
)
async def logout(response: Response, ctx: CurrentUser, redis: RedisDep) -> None:
    await service.logout(redis, ctx.session_token)
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[_marker(requires(Permission.USER_CREDENTIALS_CHANGE))],
)
async def logout_all(response: Response, ctx: CurrentUser, redis: RedisDep) -> None:
    await service.logout_all(redis, ctx.user_id)
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.post(
    "/step-up",
    dependencies=[_marker(requires(Permission.USER_CREDENTIALS_CHANGE))],
)
async def step_up(
    body: StepUpRequest, ctx: CurrentUser, session: SessionDep, redis: RedisDep
) -> dict[str, str]:
    await service.step_up(
        session,
        redis,
        token=ctx.session_token,
        user_id=ctx.user_id,
        password=body.password,
    )
    return {}


@router.get(
    "/me",
    dependencies=[_marker(requires(Permission.USER_CREDENTIALS_CHANGE))],
)
async def me(ctx: CurrentUser) -> MeResponse:
    return MeResponse(
        user_id=ctx.user_id,
        role=ctx.role,
        email=ctx.email,
        email_verified=ctx.email_verified,
    )
