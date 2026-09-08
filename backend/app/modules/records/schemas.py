"""Records wire contract (G1).

`EntrySummary` is one timeline row; `EntryDetail` adds the subtype-specific
fields, all optional because they vary by `entryType`. Clinical content is
never translated — display names and note text render as recorded
(clinical-safety.md). These schemas are real and reused by the P2.3/P2.5
implementation; only the `@stub` fixtures behind them are throwaway.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.schema import PulseSchema
from app.modules.records.models import EntryType


class EntrySummary(PulseSchema):
    id: UUID
    patient_id: UUID
    entry_type: EntryType
    occurred_at: datetime
    recorded_at: datetime
    is_critical: bool = False
    superseded_by_id: UUID | None = None
    source_provider_id: UUID | None = None
    # A short human label for the row — the diagnosis/lab/medication name, or
    # a note snippet. Recorded text, never translated.
    summary: str | None = None


class EntryDetail(EntrySummary):
    metadata: dict[str, Any] = {}
    # coded subtypes (diagnosis, procedure, lab_report, prescription)
    code_system: str | None = None
    code: str | None = None
    display_name: str | None = None
    # lab_report
    value_numeric: Decimal | None = None
    value_text: str | None = None
    unit: str | None = None
    reference_low: Decimal | None = None
    reference_high: Decimal | None = None
    # prescription
    medication_name: str | None = None
    dosage: str | None = None
    frequency: str | None = None
    route: str | None = None
    # clinical_note
    text: str | None = None
