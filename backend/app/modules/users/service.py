"""Identity business rules (G1 signatures).

No SQL, no FastAPI imports (backend.md). Other modules call these
functions; they never touch `users` tables or `users.repository`
directly.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.actor import Actor
from app.core.authz import Role
from app.modules.patients.schemas import PatientProfile
from app.modules.users.models import User


async def get_user(session: AsyncSession, user_id: UUID) -> User | None:
    raise NotImplementedError


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    raise NotImplementedError


async def register_identity(
    session: AsyncSession, *, email: str, password_hash: str, role: Role
) -> User:
    """Create the User and, for a PATIENT, a linked Patient row."""
    raise NotImplementedError


async def mark_verified(session: AsyncSession, user_id: UUID) -> None:
    raise NotImplementedError


async def change_password(
    session: AsyncSession, user_id: UUID, new_password_hash: str
) -> None:
    raise NotImplementedError


async def get_own_patient_profile(
    session: AsyncSession, actor: Actor
) -> PatientProfile | None:
    """The signed-in Patient's own profile. None if the actor owns no Patient."""
    raise NotImplementedError


async def set_locale_preference(
    session: AsyncSession, actor: Actor, locale: str
) -> None:
    raise NotImplementedError
