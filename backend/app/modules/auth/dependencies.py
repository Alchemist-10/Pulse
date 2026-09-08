"""Request-time auth: the session cookie -> AuthContext, and the route guards.

Every route must carry exactly one authorization marker — `requires(...)`
or `public()` — or the route-coverage test fails CI (ADR-0004). The
marker is attached to the dependency callable so the test can introspect
`app.routes` without executing anything.
"""

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.identity import IdentityProvider, MailpitIdentityProvider
from app.core.actor import Actor
from app.core.authz import Permission, Role, role_has_permission
from app.core.errors import ErrorCode
from app.core.exceptions import PulseError
from app.core.redis import get_redis
from app.core.sessions import has_step_up, read_session
from app.db.session import get_session
from app.modules.users import service as users_service

SESSION_COOKIE = "pulse_session"

PERMISSION_ATTR = "__pulse_permission__"
PUBLIC_ATTR = "__pulse_public__"


@dataclass(frozen=True)
class AuthContext:
    user_id: UUID
    role: Role
    email: str
    email_verified: bool
    session_token: str

    @property
    def actor(self) -> Actor:
        return Actor(user_id=self.user_id, role=self.role)


def _redis() -> Redis:
    return get_redis()


def get_identity_provider() -> IdentityProvider:
    """Overridden with FakeIdentityProvider in tests."""
    return MailpitIdentityProvider(get_redis())


async def current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(_redis),
) -> AuthContext:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise PulseError(
            ErrorCode.UNAUTHORIZED,
            "Authentication required.",
            http_status=status.HTTP_401_UNAUTHORIZED,
        )
    record = await read_session(redis, token)
    if record is None:
        raise PulseError(
            ErrorCode.SESSION_EXPIRED,
            "Your session has expired.",
            http_status=status.HTTP_401_UNAUTHORIZED,
        )
    user = await users_service.get_user(session, record.user_id)
    if user is None:
        raise PulseError(
            ErrorCode.UNAUTHORIZED,
            "Authentication required.",
            http_status=status.HTTP_401_UNAUTHORIZED,
        )
    return AuthContext(
        user_id=user.id,
        role=user.role,
        email=user.email,
        email_verified=user.email_verified_at is not None,
        session_token=token,
    )


def requires(permission: Permission) -> object:
    """Route guard: the actor's Role must hold `permission`, and (for any
    permissioned route) the email must be verified."""

    async def guard(ctx: AuthContext = Depends(current_user)) -> AuthContext:
        if not role_has_permission(ctx.role, permission):
            raise PulseError(
                ErrorCode.FORBIDDEN,
                "You do not have permission to perform this action.",
                http_status=status.HTTP_403_FORBIDDEN,
            )
        if not ctx.email_verified:
            raise PulseError(
                ErrorCode.EMAIL_NOT_VERIFIED,
                "Verify your email address to continue.",
                http_status=status.HTTP_403_FORBIDDEN,
            )
        return ctx

    setattr(guard, PERMISSION_ATTR, permission)
    return Depends(guard)


def requires_step_up() -> object:
    """Composed alongside `requires(...)` on credential-change routes."""

    async def guard(
        ctx: AuthContext = Depends(current_user),
        redis: Redis = Depends(_redis),
    ) -> AuthContext:
        if not await has_step_up(redis, ctx.session_token):
            raise PulseError(
                ErrorCode.STEP_UP_REQUIRED,
                "Re-enter your password to continue.",
                http_status=status.HTTP_403_FORBIDDEN,
            )
        return ctx

    return Depends(guard)


def public() -> object:
    """Explicit 'no authorization' marker for unauthenticated routes."""

    async def marker() -> None:
        return None

    setattr(marker, PUBLIC_ATTR, True)
    return Depends(marker)
