"""Auth business rules (G1 signatures).

No SQL, no FastAPI imports. Sessions are opaque Redis tokens (ADR-0003);
Argon2id via pwdlib. Login does NOT require a verified email — an
unverified user signs in and is gated at the permission layer instead,
so the frontend can render a "resend verification" screen.
"""

from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.identity import IdentityProvider


async def register(
    session: AsyncSession,
    idp: IdentityProvider,
    *,
    email: str,
    password: str,
    role: str,
    locale: str,
) -> UUID:
    """Create the identity, start email verification. Raises on duplicate email."""
    raise NotImplementedError


async def resend_verification(
    session: AsyncSession, idp: IdentityProvider, *, email: str, locale: str
) -> None:
    """Idempotent from the caller's view — never reveals whether the email exists."""
    raise NotImplementedError


async def complete_verification(
    session: AsyncSession, idp: IdentityProvider, *, challenge_id: str, token: str
) -> None:
    """Raises PulseError with VERIFICATION_TOKEN_INVALID / _EXPIRED on failure."""
    raise NotImplementedError


async def login(
    session: AsyncSession, redis: Redis, *, email: str, password: str
) -> str:
    """Return a fresh session token. Raises INVALID_CREDENTIALS, generically."""
    raise NotImplementedError


async def logout(redis: Redis, token: str) -> None:
    raise NotImplementedError


async def logout_all(redis: Redis, user_id: UUID) -> None:
    raise NotImplementedError


async def step_up(
    session: AsyncSession,
    redis: Redis,
    *,
    token: str,
    user_id: UUID,
    password: str,
) -> None:
    """Re-verify the password and mark this session step-up'd for a short window."""
    raise NotImplementedError
