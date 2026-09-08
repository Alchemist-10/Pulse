"""seed_marker: idempotency guard for the first-boot identity seed loader

Not schema for a domain entity -- a single-row marker the container
entrypoint's ``seed_loader`` checks so a second ``docker compose up`` is a
no-op (issue #23, "Seed loader: an entrypoint step ... guarded by a
marker row -- not an Alembic migration, since seed data is not schema").
The table is schema; the data it guards is not.

`pulse_app` gets SELECT + INSERT only -- the loader never updates or
deletes the marker, and nothing else touches this table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-08

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "seed_marker",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("dataset_sha256", sa.String(64), nullable=False),
        sa.Column(
            "applied_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.execute('GRANT SELECT, INSERT ON TABLE "seed_marker" TO pulse_app;')


def downgrade() -> None:
    op.execute('REVOKE ALL ON TABLE "seed_marker" FROM pulse_app;')
    op.drop_table("seed_marker")
