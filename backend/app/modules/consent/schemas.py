"""Consent wire contract — PROVISIONAL.

P2.0 ships these so the frontend consent screens have a shape to build
against. They are finalised in Phase 3 (P3.2) alongside the real service;
do not treat field names here as stable yet.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from app.core.schema import PulseSchema


class ConsentPurpose(StrEnum):
    TREATMENT = "TREATMENT"
    SECOND_OPINION = "SECOND_OPINION"
    OTHER = "OTHER"


class ConsentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class Consent(PulseSchema):
    id: UUID
    patient_id: UUID
    grantee_user_id: UUID
    grantee_name: str | None = None
    entry_types: list[str] | None = None
    from_date: date | None = None
    to_date: date | None = None
    purpose: ConsentPurpose
    purpose_text: str | None = None
    status: ConsentStatus
    expires_at: datetime
    granted_at: datetime
    revoked_at: datetime | None = None
    revocation_reason: str | None = None


class ConsentCreate(PulseSchema):
    grantee_user_id: UUID
    entry_types: list[str] | None = None
    from_date: date | None = None
    to_date: date | None = None
    purpose: ConsentPurpose
    purpose_text: str | None = None
    expires_at: datetime


class RevocationRequest(PulseSchema):
    reason: str | None = None
