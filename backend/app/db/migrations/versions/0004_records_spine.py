"""records spine: medical_entry trunk, five subtype tables, medical_document

Phase 2, step P2.1 (#26). Joined-table inheritance — each subtype PK *is*
an FK to `medical_entry.id`, cascading on delete (ADR-0001). `entry_type`
is the polymorphic discriminator.

`medical_entry.metadata` is JSONB and holds provenance only; no clinical
value ever lands there (clinical-safety.md). Coded clinical fields are a
`(code_system, code)` pair plus a display name.

Only `superseded_by_id` is ever UPDATEd on a clinical row, but the app
role holds full DML here to match the identity tables — append-only is
enforced by convention in the service layer, not by GRANT (that is
`audit_event`'s job, migration 0001).

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-08

"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_TABLES = (
    "medical_document",
    "lab_report",
    "diagnosis",
    "prescription",
    "procedure",
    "clinical_note",
    "medical_entry",
)

entry_type_enum = postgresql.ENUM(
    "DIAGNOSIS",
    "PRESCRIPTION",
    "LAB_REPORT",
    "PROCEDURE",
    "CLINICAL_NOTE",
    name="entry_type",
    create_type=False,
)


def _subtype_pk() -> sa.Column[Any]:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("medical_entry.id", ondelete="CASCADE"),
        primary_key=True,
    )


def upgrade() -> None:
    bind = op.get_bind()
    entry_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "medical_entry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patient.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entry_type", entry_type_enum, nullable=False),
        sa.Column(
            "source_provider_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("provider.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "author_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("is_critical", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "superseded_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("medical_entry.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_medical_entry_patient_occurred",
        "medical_entry",
        ["patient_id", "occurred_at"],
    )
    op.create_index(
        "ix_medical_entry_patient_type_occurred",
        "medical_entry",
        ["patient_id", "entry_type", "occurred_at"],
    )

    op.create_table(
        "diagnosis",
        _subtype_pk(),
        sa.Column("code_system", sa.String(255), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(512), nullable=False),
    )
    op.create_index("ix_diagnosis_code", "diagnosis", ["code_system", "code"])

    op.create_table(
        "procedure",
        _subtype_pk(),
        sa.Column("code_system", sa.String(255), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(512), nullable=False),
    )
    op.create_index("ix_procedure_code", "procedure", ["code_system", "code"])

    op.create_table(
        "prescription",
        _subtype_pk(),
        sa.Column("medication_name", sa.String(512), nullable=False),
        sa.Column("code_system", sa.String(255), nullable=True),
        sa.Column("code", sa.String(64), nullable=True),
        sa.Column("display_name", sa.String(512), nullable=True),
        sa.Column("dosage", sa.String(255), nullable=True),
        sa.Column("frequency", sa.String(255), nullable=True),
        sa.Column("route", sa.String(128), nullable=True),
    )
    op.create_index("ix_prescription_medication_name", "prescription", ["medication_name"])

    op.create_table(
        "lab_report",
        _subtype_pk(),
        sa.Column("code_system", sa.String(255), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(512), nullable=False),
        sa.Column("value_numeric", sa.Numeric(), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(64), nullable=True),
        sa.Column("reference_low", sa.Numeric(), nullable=True),
        sa.Column("reference_high", sa.Numeric(), nullable=True),
    )
    op.create_index("ix_lab_report_code", "lab_report", ["code_system", "code"])

    op.create_table(
        "clinical_note",
        _subtype_pk(),
        sa.Column("text", sa.Text(), nullable=False),
    )

    op.create_table(
        "medical_document",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "entry_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("medical_entry.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("mime_type", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_medical_document_entry_id", "medical_document", ["entry_id"])

    for table in _NEW_TABLES:
        op.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "{table}" TO pulse_app;')


def downgrade() -> None:
    for table in _NEW_TABLES:
        op.execute(f'REVOKE ALL ON TABLE "{table}" FROM pulse_app;')
    op.drop_table("medical_document")
    op.drop_table("clinical_note")
    op.drop_table("lab_report")
    op.drop_table("prescription")
    op.drop_table("procedure")
    op.drop_table("diagnosis")
    op.drop_table("medical_entry")
    entry_type_enum.drop(op.get_bind(), checkfirst=True)
