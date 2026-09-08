"""Patient profile wire contract (G1). No clinical fields — identity only."""

from datetime import date
from uuid import UUID

from app.core.schema import PulseSchema


class PatientProfile(PulseSchema):
    id: UUID
    full_name: str
    date_of_birth: date | None = None
    sex: str | None = None
    phone: str | None = None
    address_line: str | None = None
    city: str | None = None
    state: str | None = None
    locale_preference: str = "en"
    claimed: bool
