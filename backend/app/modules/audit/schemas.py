"""Audit wire contract — PROVISIONAL (finalised in Phase 3, P3.2).

The Patient's filtered projection: who looked, from where, when, at what
kind of entry. Never identifiers, never other patients' events, never
clinical content (clinical-safety.md).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.core.schema import PulseSchema


class AuditEventProjection(PulseSchema):
    id: UUID
    occurred_at: datetime
    actor_name: str
    actor_role: str
    provider_name: str | None = None
    action: str
    entry_type: str | None = None
