"""Emergency card: patient-authored, patient-controlled summary shown to
anyone who scans the QR or holds a break-glass grant. Free text typed by
the Patient into dedicated columns — never copied from Medical Entries,
never JSONB (clinical-safety.md)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmergencyCard(Base):
    __tablename__ = "emergency_card"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("patient.id", ondelete="CASCADE"), unique=True
    )
    blood_type: Mapped[str | None] = mapped_column(String(16), default=None)
    allergies: Mapped[str | None] = mapped_column(Text, default=None)
    conditions: Mapped[str | None] = mapped_column(Text, default=None)
    medications: Mapped[str | None] = mapped_column(Text, default=None)
    next_of_kin_name: Mapped[str | None] = mapped_column(String(200), default=None)
    next_of_kin_phone: Mapped[str | None] = mapped_column(String(32), default=None)
    next_of_kin_relation: Mapped[str | None] = mapped_column(String(64), default=None)
    notes: Mapped[str | None] = mapped_column(Text, default=None)
    show_blood_type: Mapped[bool] = mapped_column(Boolean, default=True)
    show_allergies: Mapped[bool] = mapped_column(Boolean, default=True)
    show_conditions: Mapped[bool] = mapped_column(Boolean, default=True)
    show_medications: Mapped[bool] = mapped_column(Boolean, default=True)
    show_next_of_kin: Mapped[bool] = mapped_column(Boolean, default=True)
    show_notes: Mapped[bool] = mapped_column(Boolean, default=False)
    qr_token: Mapped[str | None] = mapped_column(String(64), unique=True, default=None)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
