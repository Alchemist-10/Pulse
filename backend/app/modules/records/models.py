"""Records models: the MedicalEntry trunk, five subtypes, MedicalDocument.

Joined-table inheritance (ADR-0001): one `medical_entry` trunk, one table
per kind, each subtype PK *is* an FK to the trunk, cascading on delete.
`entry_type` is the polymorphic discriminator; timeline reads use
`selectin_polymorphic` so a mixed page costs one query per subtype
present, not one per row.

`MedicalEntry.entry_metadata` maps the `metadata` column — `metadata` is
reserved on a Declarative class. It is provenance only; no clinical value
(clinical-safety.md). Schema owned by migration 0004.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EntryType(StrEnum):
    DIAGNOSIS = "DIAGNOSIS"
    PRESCRIPTION = "PRESCRIPTION"
    LAB_REPORT = "LAB_REPORT"
    PROCEDURE = "PROCEDURE"
    CLINICAL_NOTE = "CLINICAL_NOTE"


class MedicalEntry(Base):
    __tablename__ = "medical_entry"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("patient.id", ondelete="CASCADE")
    )
    entry_type: Mapped[EntryType] = mapped_column(SAEnum(EntryType, name="entry_type"))
    source_provider_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("provider.id", ondelete="SET NULL"),
        default=None,
    )
    author_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), default=None
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_critical: Mapped[bool] = mapped_column(Boolean, server_default=func.false())
    superseded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("medical_entry.id", ondelete="SET NULL"),
        default=None,
    )
    entry_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    __mapper_args__ = {
        "polymorphic_on": entry_type,
        "polymorphic_identity": "medical_entry",
    }


def _subtype_pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("medical_entry.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Diagnosis(MedicalEntry):
    __tablename__ = "diagnosis"

    id: Mapped[uuid.UUID] = _subtype_pk()
    code_system: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(64))
    display_name: Mapped[str] = mapped_column(String(512))

    __mapper_args__ = {"polymorphic_identity": EntryType.DIAGNOSIS}


class Procedure(MedicalEntry):
    __tablename__ = "procedure"

    id: Mapped[uuid.UUID] = _subtype_pk()
    code_system: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(64))
    display_name: Mapped[str] = mapped_column(String(512))

    __mapper_args__ = {"polymorphic_identity": EntryType.PROCEDURE}


class Prescription(MedicalEntry):
    __tablename__ = "prescription"

    id: Mapped[uuid.UUID] = _subtype_pk()
    medication_name: Mapped[str] = mapped_column(String(512))
    code_system: Mapped[str | None] = mapped_column(String(255), default=None)
    code: Mapped[str | None] = mapped_column(String(64), default=None)
    display_name: Mapped[str | None] = mapped_column(String(512), default=None)
    dosage: Mapped[str | None] = mapped_column(String(255), default=None)
    frequency: Mapped[str | None] = mapped_column(String(255), default=None)
    route: Mapped[str | None] = mapped_column(String(128), default=None)

    __mapper_args__ = {"polymorphic_identity": EntryType.PRESCRIPTION}


class LabReport(MedicalEntry):
    __tablename__ = "lab_report"

    id: Mapped[uuid.UUID] = _subtype_pk()
    code_system: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(64))
    display_name: Mapped[str] = mapped_column(String(512))
    value_numeric: Mapped[float | None] = mapped_column(Numeric, default=None)
    value_text: Mapped[str | None] = mapped_column(Text, default=None)
    unit: Mapped[str | None] = mapped_column(String(64), default=None)
    reference_low: Mapped[float | None] = mapped_column(Numeric, default=None)
    reference_high: Mapped[float | None] = mapped_column(Numeric, default=None)

    __mapper_args__ = {"polymorphic_identity": EntryType.LAB_REPORT}


class ClinicalNote(MedicalEntry):
    __tablename__ = "clinical_note"

    id: Mapped[uuid.UUID] = _subtype_pk()
    text: Mapped[str] = mapped_column(Text)

    __mapper_args__ = {"polymorphic_identity": EntryType.CLINICAL_NOTE}


class MedicalDocument(Base):
    __tablename__ = "medical_document"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entry_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("medical_entry.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    storage_path: Mapped[str] = mapped_column(String(1024))
    checksum_sha256: Mapped[str] = mapped_column(String(64))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
