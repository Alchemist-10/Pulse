from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.core.schema import PulseSchema


class EmergencyCardFields(PulseSchema):
    blood_type: str | None = Field(default=None, max_length=16)
    allergies: str | None = Field(default=None, max_length=2000)
    conditions: str | None = Field(default=None, max_length=2000)
    medications: str | None = Field(default=None, max_length=2000)
    next_of_kin_name: str | None = Field(default=None, max_length=200)
    next_of_kin_phone: str | None = Field(default=None, max_length=32)
    next_of_kin_relation: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=2000)


class EmergencyCardVisibility(PulseSchema):
    show_blood_type: bool = True
    show_allergies: bool = True
    show_conditions: bool = True
    show_medications: bool = True
    show_next_of_kin: bool = True
    show_notes: bool = False


class EmergencyCardUpdate(EmergencyCardFields, EmergencyCardVisibility):
    pass


class EmergencyCard(EmergencyCardUpdate):
    """The owner's full view: every field plus what is shared, and the QR
    token if enabled."""

    qr_token: str | None = None
    updated_at: datetime | None = None


class EmergencyCardView(PulseSchema):
    """What a scanner / break-glass clinician sees: only fields the Patient
    chose to show. Hidden fields are null, indistinguishable from empty."""

    patient_id: UUID
    patient_name: str
    blood_type: str | None = None
    allergies: str | None = None
    conditions: str | None = None
    medications: str | None = None
    next_of_kin_name: str | None = None
    next_of_kin_phone: str | None = None
    next_of_kin_relation: str | None = None
    notes: str | None = None
