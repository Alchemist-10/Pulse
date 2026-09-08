"""Identity repository — all SQL for User / Patient / Provider / ProviderStaff.

Phase 1 G1 contract: signatures merge first raising NotImplementedError,
implementations second (delivery-plan.md). Services call these; they
never build queries. Writes flush but do not commit — the calling
service owns the transaction boundary.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import Role
from app.modules.users.models import Patient, Provider, ProviderStaff, User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    return await session.get(User, user_id)


async def create_user(
    session: AsyncSession, *, email: str, password_hash: str, role: Role
) -> User:
    user = User(email=email, password_hash=password_hash, role=role)
    session.add(user)
    await session.flush()
    return user


async def set_password_hash(
    session: AsyncSession, user_id: UUID, password_hash: str
) -> None:
    await session.execute(
        update(User).where(User.id == user_id).values(password_hash=password_hash)
    )


async def mark_email_verified(
    session: AsyncSession, user_id: UUID, verified_at: datetime
) -> None:
    await session.execute(
        update(User).where(User.id == user_id).values(email_verified_at=verified_at)
    )


async def get_patient_by_id(session: AsyncSession, patient_id: UUID) -> Patient | None:
    return await session.get(Patient, patient_id)


async def get_patient_by_user_id(session: AsyncSession, user_id: UUID) -> Patient | None:
    result = await session.execute(select(Patient).where(Patient.user_id == user_id))
    return result.scalar_one_or_none()


async def create_patient(
    session: AsyncSession, *, user_id: UUID | None, full_name: str, **fields: object
) -> Patient:
    patient = Patient(user_id=user_id, full_name=full_name)
    for key, value in fields.items():
        setattr(patient, key, value)
    session.add(patient)
    await session.flush()
    return patient


async def set_patient_locale(
    session: AsyncSession, patient_id: UUID, locale: str
) -> None:
    await session.execute(
        update(Patient).where(Patient.id == patient_id).values(locale_preference=locale)
    )


async def get_provider_by_id(session: AsyncSession, provider_id: UUID) -> Provider | None:
    return await session.get(Provider, provider_id)


async def get_provider_staff_by_user_id(
    session: AsyncSession, user_id: UUID
) -> ProviderStaff | None:
    result = await session.execute(
        select(ProviderStaff).where(ProviderStaff.user_id == user_id)
    )
    return result.scalar_one_or_none()
