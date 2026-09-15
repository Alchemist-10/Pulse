"""Providers business rules (P2.5).

Resolves which Provider a Provider Staff user acts for, and reads a
Provider's public identity. No clinical data. All storage lives in the
identity cluster, reached through `users.service`.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.actor import Actor
from app.core.errors import ErrorCode
from app.core.exceptions import PulseError
from app.modules.providers.schemas import Provider
from app.modules.users import service as users_service


async def provider_for_current_staff(session: AsyncSession, actor: Actor) -> UUID | None:
    return await users_service.get_provider_for_staff(session, actor.user_id)


async def get_provider(session: AsyncSession, actor: Actor, provider_id: UUID) -> Provider:
    row = await users_service.get_provider(session, provider_id)
    if row is None:
        raise PulseError(ErrorCode.NOT_FOUND, "No such provider.", http_status=404)
    return Provider(
        id=row.id,
        name=row.name,
        kind=row.kind.value,
        city=row.city,
        state=row.state,
    )
