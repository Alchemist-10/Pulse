"""Identity repository — all SQL for User / Patient / Provider / ProviderStaff.

Phase 1 G1 contract: signatures merge first raising NotImplementedError,
implementations second (delivery-plan.md). Services call these; they
never build queries.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import Role
from app.modules.users.models import Patient, Provider, ProviderStaff, User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    raise NotImplementedError


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    raise NotImplementedError


async def create_user(
    session: AsyncSession, *, email: str, password_hash: str, role: Role
) -> User:
    raise NotImplementedError


async def set_password_hash(
    session: AsyncSession, user_id: UUID, password_hash: str
) -> None:
    raise NotImplementedError


async def mark_email_verified(
    session: AsyncSession, user_id: UUID, verified_at: datetime
) -> None:
    raise NotImplementedError


async def get_patient_by_id(session: AsyncSession, patient_id: UUID) -> Patient | None:
    raise NotImplementedError


async def get_patient_by_user_id(session: AsyncSession, user_id: UUID) -> Patient | None:
    raise NotImplementedError


async def create_patient(
    session: AsyncSession, *, user_id: UUID | None, full_name: str, **fields: object
) -> Patient:
    raise NotImplementedError


async def set_patient_locale(
    session: AsyncSession, patient_id: UUID, locale: str
) -> None:
    raise NotImplementedError


async def get_provider_by_id(session: AsyncSession, provider_id: UUID) -> Provider | None:
    raise NotImplementedError


async def get_provider_staff_by_user_id(
    session: AsyncSession, user_id: UUID
) -> ProviderStaff | None:
    raise NotImplementedError
