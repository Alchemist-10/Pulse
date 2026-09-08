"""Providers wire contract (P2.5). Public organisational identity only."""

from uuid import UUID

from app.core.schema import PulseSchema


class Provider(PulseSchema):
    id: UUID
    name: str
    kind: str
    city: str
    state: str
