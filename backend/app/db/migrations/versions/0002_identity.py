"""identity tables: user, provider, patient, provider_staff

Phase 1. Establishes the identity cluster and grants the app role
(`pulse_app`) full CRUD on these four tables. `audit_event` and its
INSERT/SELECT-only grant remain Phase 3 (see migration 0001).

`patient.user_id` is nullable by design — the Unclaimed Patient
(domain-model.md).

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-08

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_APP_TABLES = ("user", "provider", "patient", "provider_staff")

# create_type=False: these are created/dropped explicitly in up/downgrade.
# Without it, op.create_table() emits a second unconditional CREATE TYPE and
# `alembic upgrade head` fails on a clean DB with "type already exists".
role_enum = postgresql.ENUM(
    "PATIENT",
    "CLINICIAN",
    "PROVIDER_STAFF",
    "ADMINISTRATOR",
    name="role",
    create_type=False,
)
sex_enum = postgresql.ENUM("MALE", "FEMALE", "OTHER", name="sex", create_type=False)
provider_kind_enum = postgresql.ENUM(
    "HOSPITAL", "CLINIC", "LAB", name="provider_kind", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    role_enum.create(bind, checkfirst=True)
    sex_enum.create(bind, checkfirst=True)
    provider_kind_enum.create(bind, checkfirst=True)

    op.create_table(
        "user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_user_email", "user", ["email"], unique=True)

    op.create_table(
        "provider",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("kind", provider_kind_enum, nullable=False),
        sa.Column("city", sa.String(120), nullable=False),
        sa.Column("state", sa.String(120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "patient",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("sex", sex_enum, nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("address_line", sa.String(255), nullable=True),
        sa.Column("city", sa.String(120), nullable=True),
        sa.Column("state", sa.String(120), nullable=True),
        sa.Column("locale_preference", sa.String(8), nullable=False, server_default="en"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_patient_user_id", "patient", ["user_id"], unique=True)
    op.create_index("ix_patient_phone", "patient", ["phone"])

    op.create_table(
        "provider_staff",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "provider_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("provider.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_provider_staff_user_id", "provider_staff", ["user_id"], unique=True
    )
    op.create_index(
        "ix_provider_staff_provider_id", "provider_staff", ["provider_id"]
    )

    for table in _APP_TABLES:
        op.execute(
            f'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "{table}" TO pulse_app;'
        )


def downgrade() -> None:
    for table in _APP_TABLES:
        op.execute(f'REVOKE ALL ON TABLE "{table}" FROM pulse_app;')
    op.drop_table("provider_staff")
    op.drop_table("patient")
    op.drop_table("provider")
    op.drop_table("user")
    bind = op.get_bind()
    provider_kind_enum.drop(bind, checkfirst=True)
    sex_enum.drop(bind, checkfirst=True)
    role_enum.drop(bind, checkfirst=True)
