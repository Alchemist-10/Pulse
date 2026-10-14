from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.emergency.models import EmergencyCard


async def get_by_patient(session: AsyncSession, patient_id: UUID) -> EmergencyCard | None:
    result = await session.scalars(
        select(EmergencyCard).where(EmergencyCard.patient_id == patient_id)
    )
    return result.first()


async def get_by_token(session: AsyncSession, token: str) -> EmergencyCard | None:
    result = await session.scalars(select(EmergencyCard).where(EmergencyCard.qr_token == token))
    return result.first()


async def upsert(session: AsyncSession, patient_id: UUID, values: dict[str, Any]) -> EmergencyCard:
    card = await get_by_patient(session, patient_id)
    if card is None:
        card = EmergencyCard(patient_id=patient_id, **values)
        session.add(card)
    else:
        for key, value in values.items():
            setattr(card, key, value)
    await session.flush()
    await session.refresh(card)
    return card
