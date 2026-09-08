"""Identity business rules (G1 signatures).

No SQL, no FastAPI imports (backend.md). Other modules call these
functions; they never touch `users` tables or `users.repository`
directly. Mutations commit here — repository writes only flush.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.actor import Actor
from app.core.authz import Role
from app.modules.patients.schemas import PatientProfile
from app.modules.users import repository
from app.modules.users.models import Patient, User


def _to_profile(patient: Patient) -> PatientProfile:
    return PatientProfile(
        id=patient.id,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth,
        sex=patient.sex.value if patient.sex is not None else None,
        phone=patient.phone,
        address_line=patient.address_line,
        city=patient.city,
        state=patient.state,
        locale_preference=patient.locale_preference,
        claimed=patient.user_id is not None,
    )


async def get_user(session: AsyncSession, user_id: UUID) -> User | None:
    return await repository.get_user_by_id(session, user_id)


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    return await repository.get_user_by_email(session, email)


async def register_identity(
    session: AsyncSession, *, email: str, password_hash: str, role: Role
) -> User:
    """Create the User and, for a PATIENT, a linked Patient row."""
    user = await repository.create_user(
        session, email=email, password_hash=password_hash, role=role
    )
    if role is Role.PATIENT:
        placeholder_name = email.split("@", 1)[0]
        await repository.create_patient(
            session, user_id=user.id, full_name=placeholder_name
        )
    await session.commit()
    return user


async def mark_verified(session: AsyncSession, user_id: UUID) -> None:
    await repository.mark_email_verified(session, user_id, datetime.now(UTC))
    await session.commit()


async def change_password(
    session: AsyncSession, user_id: UUID, new_password_hash: str
) -> None:
    await repository.set_password_hash(session, user_id, new_password_hash)
    await session.commit()


async def get_own_patient_profile(
    session: AsyncSession, actor: Actor
) -> PatientProfile | None:
    """The signed-in Patient's own profile. None if the actor owns no Patient."""
    patient = await repository.get_patient_by_user_id(session, actor.user_id)
    if patient is None:
        return None
    return _to_profile(patient)


async def set_locale_preference(
    session: AsyncSession, actor: Actor, locale: str
) -> None:
    patient = await repository.get_patient_by_user_id(session, actor.user_id)
    if patient is None:
        return
    await repository.set_patient_locale(session, patient.id, locale)
    await session.commit()
