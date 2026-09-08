"""Phase 2 (records spine) test helpers.

Imported as top-level ``records_helpers`` (never ``tests.records_helpers``),
matching the convention in ``helpers.py`` so mypy resolves one module name.

These helpers write ``medical_entry`` / subtype / ``provider`` rows with raw
SQL against a short-lived engine — the same shape as ``helpers.identity_session``.
Everything that touches ``medical_entry`` fails until migration 0004 lands; that
is deliberate. The Phase 2 tests are written red, ahead of the implementation
(delivery-plan "write the negative test first").
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import create_async_engine

_ENTRY_COLUMNS = (
    "id",
    "patient_id",
    "entry_type",
    "source_provider_id",
    "author_user_id",
    "occurred_at",
    "recorded_at",
    "is_critical",
    "superseded_by_id",
    "metadata",
)


async def user_id_for_email(app_database_url: str, email: str) -> uuid.UUID:
    engine = create_async_engine(app_database_url)
    try:
        async with engine.connect() as conn:
            row = await conn.execute(
                text('SELECT id FROM "user" WHERE email = :email'), {"email": email}
            )
            return uuid.UUID(str(row.scalar_one()))
    finally:
        await engine.dispose()


async def seed_provider_staff(
    app_database_url: str,
    *,
    user_email: str,
    provider_name: str = "Apollo Speciality Hospital",
    kind: str = "HOSPITAL",
    city: str = "Chennai",
    state: str = "Tamil Nadu",
) -> uuid.UUID:
    """Create a Provider and link the (already-registered) user to it as
    Provider Staff. Returns the provider id."""
    provider_id = uuid.uuid4()
    user_id = await user_id_for_email(app_database_url, user_email)
    engine = create_async_engine(app_database_url)
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO provider (id, name, kind, city, state) "
                    "VALUES (:id, :name, :kind, :city, :state)"
                ),
                {
                    "id": provider_id,
                    "name": provider_name,
                    "kind": kind,
                    "city": city,
                    "state": state,
                },
            )
            await conn.execute(
                text(
                    "INSERT INTO provider_staff (id, user_id, provider_id) "
                    "VALUES (:id, :user_id, :provider_id)"
                ),
                {
                    "id": uuid.uuid4(),
                    "user_id": user_id,
                    "provider_id": provider_id,
                },
            )
    finally:
        await engine.dispose()
    return provider_id


async def insert_entry(
    app_database_url: str,
    *,
    patient_id: uuid.UUID,
    occurred_at: datetime,
    entry_type: str = "CLINICAL_NOTE",
    recorded_at: datetime | None = None,
    is_critical: bool = False,
    superseded_by_id: uuid.UUID | None = None,
    source_provider_id: uuid.UUID | None = None,
    author_user_id: uuid.UUID | None = None,
    # CLINICAL_NOTE
    note_text: str = "Patient stable. Continue current management.",
    # LAB_REPORT
    code_system: str = "http://loinc.org",
    code: str = "4548-4",
    display_name: str = "Hemoglobin A1c",
    value_numeric: float | None = 7.8,
    value_text: str | None = None,
    unit: str | None = "%",
    reference_low: float | None = 4.0,
    reference_high: float | None = 5.6,
) -> uuid.UUID:
    """Insert one medical_entry + its subtype row. Returns the entry id."""
    entry_id = uuid.uuid4()
    params = {
        "id": entry_id,
        "patient_id": patient_id,
        "entry_type": entry_type,
        "source_provider_id": source_provider_id,
        "author_user_id": author_user_id,
        "occurred_at": occurred_at,
        "recorded_at": recorded_at or occurred_at,
        "is_critical": is_critical,
        "superseded_by_id": superseded_by_id,
        "metadata": json.dumps({"import_batch": "test"}),
    }
    engine = create_async_engine(app_database_url)
    try:
        async with engine.begin() as conn:
            placeholders = ", ".join(f":{c}" for c in _ENTRY_COLUMNS)
            await conn.execute(
                text(
                    f"INSERT INTO medical_entry ({', '.join(_ENTRY_COLUMNS)}) "
                    f"VALUES ({placeholders})"
                ),
                params,
            )
            if entry_type == "CLINICAL_NOTE":
                await conn.execute(
                    text("INSERT INTO clinical_note (id, text) VALUES (:id, :text)"),
                    {"id": entry_id, "text": note_text},
                )
            elif entry_type == "LAB_REPORT":
                await conn.execute(
                    text(
                        "INSERT INTO lab_report "
                        "(id, code_system, code, display_name, value_numeric, "
                        " value_text, unit, reference_low, reference_high) "
                        "VALUES (:id, :code_system, :code, :display_name, "
                        ":value_numeric, :value_text, :unit, :reference_low, "
                        ":reference_high)"
                    ),
                    {
                        "id": entry_id,
                        "code_system": code_system,
                        "code": code,
                        "display_name": display_name,
                        "value_numeric": value_numeric,
                        "value_text": value_text,
                        "unit": unit,
                        "reference_low": reference_low,
                        "reference_high": reference_high,
                    },
                )
            else:  # pragma: no cover - extend when a test needs another subtype
                raise ValueError(f"insert_entry does not yet handle {entry_type}")
    finally:
        await engine.dispose()
    return entry_id


async def stamp_superseded(
    app_database_url: str, *, original_id: uuid.UUID, replacement_id: uuid.UUID
) -> int:
    """The one UPDATE Phase 2 permits on a clinical row. Returns rows affected."""
    engine = create_async_engine(app_database_url)
    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text(
                    "UPDATE medical_entry SET superseded_by_id = :new "
                    "WHERE id = :old AND superseded_by_id IS NULL"
                ),
                {"new": replacement_id, "old": original_id},
            )
            return result.rowcount
    finally:
        await engine.dispose()


async def wipe_records(app_database_url: str) -> None:
    """Child-first delete so FKs never block. Each table in its own
    transaction, and a missing table (migration 0004 not yet merged) is
    swallowed so identity/provider cleanup still runs."""
    engine = create_async_engine(app_database_url)
    try:
        for table in (
            "medical_document",
            "lab_report",
            "diagnosis",
            "prescription",
            "procedure",
            "clinical_note",
            "medical_entry",
            "provider_staff",
            "provider",
        ):
            try:
                async with engine.begin() as conn:
                    await conn.execute(text(f"DELETE FROM {table}"))
            except ProgrammingError:
                pass  # relation does not exist yet
    finally:
        await engine.dispose()
