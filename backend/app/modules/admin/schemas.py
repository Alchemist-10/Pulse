"""Admin wire contract (P4.3, #54).

ADR-0007: an Administrator reads no clinical data, on any endpoint, ever.
`AdminPatientIdentity` carries identity fields and an entry *count* only
— never entry content (ADR-0011, the duplicate-review interface).
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from app.core.schema import PulseSchema


class AdminPatientIdentity(PulseSchema):
    id: UUID
    full_name: str
    date_of_birth: date | None
    phone: str | None
    claimed: bool
    entry_count: int


class DuplicateReviewCandidate(PulseSchema):
    id: UUID
    patient_a: AdminPatientIdentity
    patient_b: AdminPatientIdentity
    score: float
    status: str


class NotDuplicateRequest(PulseSchema):
    patient_id_a: UUID
    patient_id_b: UUID


class MergeRequest(PulseSchema):
    winner_patient_id: UUID
    loser_patient_id: UUID


class MergeResult(PulseSchema):
    id: UUID
    winner_patient_id: UUID
    loser_patient_id: UUID
    occurred_at: datetime
    reversed_at: datetime | None


class MergeRecord(MergeResult):
    """A reversible merge with both Patients' names — identity only, never
    clinical content (ADR-0007)."""

    winner_name: str
    loser_name: str


class AdminPatientRow(AdminPatientIdentity):
    sex: str | None
    city: str | None
    state: str | None
    created_at: datetime


class AdminPatientDetail(AdminPatientRow):
    """Drilldown: identity + counts. Never entry content (ADR-0007)."""

    address_line: str | None
    locale_preference: str
    active_consent_count: int
    total_consent_count: int
    audit_event_count: int


class AdminUserRow(PulseSchema):
    id: UUID
    email: str
    role: str
    email_verified: bool
    created_at: datetime


class AdminSummary(PulseSchema):
    patients: int
    claimed_patients: int
    pending_duplicates: int
    users_patient: int = 0
    users_clinician: int = 0
    users_provider_staff: int = 0
    users_administrator: int = 0
