"""Emergency card, optional consent expiry, card-view audit/notification types.

Revision ID: 0010
Revises: 0009
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'EMERGENCY_CARD_VIEWED'")
        op.execute(
            "ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'EMERGENCY_CARD_VIEWED'"
        )
    op.alter_column("consent", "expires_at", nullable=True)
    op.alter_column("access_permission", "expires_at", nullable=True)
    op.create_table(
        "emergency_card",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("patient.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("blood_type", sa.String(16), nullable=True),
        sa.Column("allergies", sa.Text, nullable=True),
        sa.Column("conditions", sa.Text, nullable=True),
        sa.Column("medications", sa.Text, nullable=True),
        sa.Column("next_of_kin_name", sa.String(200), nullable=True),
        sa.Column("next_of_kin_phone", sa.String(32), nullable=True),
        sa.Column("next_of_kin_relation", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("show_blood_type", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("show_allergies", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("show_conditions", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("show_medications", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("show_next_of_kin", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("show_notes", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("qr_token", sa.String(64), nullable=True, unique=True),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.execute(
        'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "emergency_card" TO pulse_app;'
    )


def downgrade() -> None:
    op.drop_table("emergency_card")
    # Enum values retained (audit history). Existing no-expiry rows cannot be
    # expressed as NOT NULL; leave the columns nullable.
