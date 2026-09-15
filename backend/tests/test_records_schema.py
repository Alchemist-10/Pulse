"""P2.1 — the medical_entry trunk, five subtype tables, medical_document, and
the five load-bearing indexes.

Migration/schema-inspection seam: no app, no HTTP. Reads the migrated test
database through SQLAlchemy's Inspector. Prior art: migration 0001's GRANT /
pg_trgm proof tests.

Written red: migration 0004 does not exist yet, so every assertion here fails
until the trunk lands. Delivery-plan: "write the negative test first".
"""

from __future__ import annotations

from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine

_SUBTYPES = ("diagnosis", "prescription", "lab_report", "procedure", "clinical_note")


def _snapshot(sync_conn: Any) -> dict[str, Any]:
    insp = inspect(sync_conn)
    tables = set(insp.get_table_names())
    out: dict[str, Any] = {"tables": tables, "columns": {}, "fks": {}, "indexes": {}}
    for t in tables:
        out["columns"][t] = {c["name"]: c for c in insp.get_columns(t)}
        out["fks"][t] = insp.get_foreign_keys(t)
        out["indexes"][t] = insp.get_indexes(t)
        out["pk"] = out.get("pk", {})
        out["pk"][t] = insp.get_pk_constraint(t)
    return out


@pytest_asyncio.fixture
async def schema(db_engine: AsyncEngine) -> dict[str, Any]:
    async with db_engine.connect() as conn:
        return await conn.run_sync(_snapshot)


def test_trunk_and_subtype_tables_exist(schema: dict[str, Any]) -> None:
    expected = {"medical_entry", "medical_document", *_SUBTYPES}
    assert expected <= schema["tables"], sorted(expected - schema["tables"])


@pytest.mark.parametrize("subtype", _SUBTYPES)
def test_subtype_pk_is_a_cascading_fk_to_the_trunk(schema: dict[str, Any], subtype: str) -> None:
    assert subtype in schema["tables"]
    pk_cols = schema["pk"][subtype]["constrained_columns"]
    assert pk_cols == ["id"], f"{subtype} PK is {pk_cols}, expected ['id']"
    to_trunk = [
        fk
        for fk in schema["fks"][subtype]
        if fk["referred_table"] == "medical_entry" and fk["constrained_columns"] == ["id"]
    ]
    assert to_trunk, f"{subtype}.id is not an FK to medical_entry.id"
    assert (to_trunk[0].get("options") or {}).get("ondelete", "").upper() == "CASCADE"


def test_superseded_by_id_is_a_nullable_self_fk(schema: dict[str, Any]) -> None:
    cols = schema["columns"]["medical_entry"]
    assert "superseded_by_id" in cols
    assert cols["superseded_by_id"]["nullable"] is True
    self_fks = [
        fk
        for fk in schema["fks"]["medical_entry"]
        if fk["referred_table"] == "medical_entry"
        and fk["constrained_columns"] == ["superseded_by_id"]
    ]
    assert self_fks, "superseded_by_id does not reference medical_entry.id"


def test_metadata_is_jsonb(schema: dict[str, Any]) -> None:
    col = schema["columns"]["medical_entry"]["metadata"]
    assert "JSON" in str(col["type"]).upper()


def test_lab_report_carries_numeric_and_text_value_columns(
    schema: dict[str, Any],
) -> None:
    cols = schema["columns"]["lab_report"]
    for name in ("value_numeric", "reference_low", "reference_high"):
        assert name in cols, name
        assert "NUMERIC" in str(cols[name]["type"]).upper()
    assert "value_text" in cols
    assert (
        "TEXT" in str(cols["value_text"]["type"]).upper()
        or "VARCHAR" in str(cols["value_text"]["type"]).upper()
    )


def _has_index_on(indexes: list[dict[str, Any]], columns: list[str]) -> bool:
    return any(list(ix["column_names"]) == columns for ix in indexes)


def test_the_five_named_indexes_exist(schema: dict[str, Any]) -> None:
    idx = schema["indexes"]
    assert _has_index_on(idx["medical_entry"], ["patient_id", "occurred_at"])
    assert _has_index_on(idx["medical_entry"], ["patient_id", "entry_type", "occurred_at"])
    assert _has_index_on(idx["lab_report"], ["code_system", "code"])
    assert _has_index_on(idx["diagnosis"], ["code_system", "code"])
    assert _has_index_on(idx["prescription"], ["medication_name"])


def test_medical_document_metadata_columns(schema: dict[str, Any]) -> None:
    cols = schema["columns"]["medical_document"]
    for name in (
        "entry_id",
        "filename",
        "mime_type",
        "size_bytes",
        "storage_path",
        "checksum_sha256",
        "uploaded_at",
    ):
        assert name in cols, name
    assert any(
        fk["referred_table"] == "medical_entry" and fk["constrained_columns"] == ["entry_id"]
        for fk in schema["fks"]["medical_document"]
    )
