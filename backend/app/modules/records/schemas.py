"""Records wire contract (G1).

`EntrySummary` is one timeline row; `EntryDetail` adds the subtype-specific
fields, all optional because they vary by `entryType`. Clinical content is
never translated — display names and note text render as recorded
(clinical-safety.md). These schemas are real and reused by the P2.3/P2.5
implementation; only the `@stub` fixtures behind them are throwaway.
"""

from __future__ import annotations

from datetime import datetime
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


class Document(PulseSchema):
    id: UUID
    entry_id: UUID
    filename: str
    mime_type: str
    size_bytes: int
    checksum_sha256: str
    uploaded_at: datetime


class EntryDetail(EntrySummary):
    metadata: dict[str, Any] = {}
    supersedes_id: UUID | None = None
    documents: list[Document] = []
    # coded subtypes (diagnosis, procedure, lab_report, prescription)
    code_system: str | None = None
    code: str | None = None
    display_name: str | None = None
    # lab_report
    value_numeric: float | None = None
    value_text: str | None = None
    unit: str | None = None
    reference_low: float | None = None
    reference_high: float | None = None
    # prescription
    medication_name: str | None = None
    dosage: str | None = None
    frequency: str | None = None
    route: str | None = None
    # clinical_note
    text: str | None = None


class EntryCreate(PulseSchema):
    """What a Provider files, or what a correction re-files (P2.5 / P2.7).

    Subtype fields are optional at the wire; the service validates the set
    required for `entry_type`. There is deliberately no `metadata` field —
    `medical_entry.metadata` is provenance only and set by the import
    pipeline, never by an API caller (clinical-safety.md: no clinical value
    in JSONB, "not temporarily").
    """

    entry_type: EntryType
    occurred_at: datetime
    is_critical: bool = False
    source_provider_id: UUID | None = None
    code_system: str | None = None
    code: str | None = None
    display_name: str | None = None
    value_numeric: float | None = None
    value_text: str | None = None
    unit: str | None = None
    reference_low: float | None = None
    reference_high: float | None = None
    medication_name: str | None = None
    dosage: str | None = None
    frequency: str | None = None
    route: str | None = None
    text: str | None = None


class DocumentCreate(PulseSchema):
    """Stored-file metadata handed to the repository after the bytes land
    behind the StorageProvider (P2.6). No clinical content."""

    filename: str
    mime_type: str
    size_bytes: int
    storage_path: str
    checksum_sha256: str
