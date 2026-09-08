"""First-boot seed loader against a real, freshly migrated PostgreSQL.

Self-contained: spins its own ``postgres:18.6`` container, runs
``alembic upgrade head``, then exercises ``app.db.seed_loader``. Does not
touch ``backend/tests/conftest.py``.

Asserts:
* loader vs an empty migrated DB -> deterministic row counts
* >= 1 Patient with ``user_id IS NULL`` (the Unclaimed Patient)
* run twice -> row counts unchanged (idempotent, marker-guarded)
* >= 1 planted duplicate pair and >= 1 near-miss pair present and
  identifiable in the loaded rows
"""

from __future__ import annotations

import csv
import os
from collections.abc import Iterator
from pathlib import Path

import pytest
import pytest_asyncio

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_DIR = _REPO_ROOT / "backend"
_IDENTITY_DIR = _REPO_ROOT / "seed" / "data" / "identity"


@pytest.fixture(scope="module")
def _migrated_db() -> Iterator[str]:
    from alembic import command
    from alembic.config import Config
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer(
        "postgres:18.6", username="pulse", password="pulse", dbname="pulse"
    ) as pg:
        host = pg.get_container_host_ip()
        port = pg.get_exposed_port(5432)
        admin_url = f"postgresql+asyncpg://pulse:pulse@{host}:{port}/pulse"
        app_url = f"postgresql+asyncpg://pulse_app:pulse_app@{host}:{port}/pulse"

        os.environ["ALEMBIC_DATABASE_URL"] = admin_url
        os.environ["DATABASE_URL"] = app_url
        os.environ["SEED_DATA_DIR"] = str(_REPO_ROOT / "seed" / "data")

        cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
        cfg.set_main_option("script_location", str(_BACKEND_DIR / "app/db/migrations"))
        command.upgrade(cfg, "head")
        yield app_url


@pytest_asyncio.fixture(autouse=True)
async def _dispose_app_engine() -> Iterator[None]:
    """pytest-asyncio gives each test its own event loop; the module-level
    engine in ``app.db.session`` would otherwise carry a pool bound to the
    previous test's loop into the next one."""
    yield
    from app.db.session import engine

    await engine.dispose()


async def _table_counts(app_url: str) -> dict[str, int]:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(app_url)
    try:
        async with engine.connect() as conn:
            out = {}
            for t in ("provider", '"user"', "patient", "provider_staff", "seed_marker"):
                out[t.strip('"')] = (
                    await conn.execute(text(f"SELECT count(*) FROM {t}"))
                ).scalar_one()
            out["patient_unclaimed"] = (
                await conn.execute(
                    text("SELECT count(*) FROM patient WHERE user_id IS NULL")
                )
            ).scalar_one()
            return out
    finally:
        await engine.dispose()


def _expected_counts() -> dict[str, int]:
    def n(name: str) -> int:
        with (_IDENTITY_DIR / name).open(encoding="utf-8") as fh:
            return sum(1 for _ in csv.DictReader(fh))

    return {
        "provider": n("providers.csv"),
        "user": n("users.csv"),
        "patient": n("patients.csv"),
        "provider_staff": n("provider_staff.csv"),
    }


@pytest.mark.asyncio
async def test_loader_populates_migrated_db(_migrated_db: str) -> None:
    from app.db.seed_loader import run_seed

    result = await run_seed()
    assert result.skipped is False

    counts = await _table_counts(_migrated_db)
    expected = _expected_counts()
    assert counts["provider"] == expected["provider"]
    assert counts["user"] == expected["user"]
    assert counts["patient"] == expected["patient"]
    assert counts["provider_staff"] == expected["provider_staff"]
    assert counts["seed_marker"] == 1


@pytest.mark.asyncio
async def test_at_least_one_unclaimed_patient(_migrated_db: str) -> None:
    counts = await _table_counts(_migrated_db)
    assert counts["patient_unclaimed"] >= 1


@pytest.mark.asyncio
async def test_second_run_is_a_noop(_migrated_db: str) -> None:
    from app.db.seed_loader import run_seed

    before = await _table_counts(_migrated_db)
    result = await run_seed()
    assert result.skipped is True
    after = await _table_counts(_migrated_db)
    assert before == after


@pytest.mark.asyncio
async def test_planted_pairs_present_and_identifiable(_migrated_db: str) -> None:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    with (_IDENTITY_DIR / "planted_pairs.csv").open(encoding="utf-8") as fh:
        pairs = list(csv.DictReader(fh))

    dups = [p for p in pairs if p["kind"] == "duplicate"]
    misses = [p for p in pairs if p["kind"] == "near_miss"]
    assert len(dups) >= 1
    assert len(misses) >= 1

    async def _patient(conn: object, pid: str) -> dict[str, object] | None:
        row = (
            await conn.execute(  # type: ignore[attr-defined]
                text(
                    "SELECT full_name, date_of_birth, phone "
                    "FROM patient WHERE id = :id"
                ),
                {"id": pid},
            )
        ).mappings().first()
        return dict(row) if row is not None else None

    engine = create_async_engine(_migrated_db)
    try:
        async with engine.connect() as conn:
            for pair in (*dups[:1], *misses[:1]):
                for side in ("patient_id_a", "patient_id_b"):
                    assert (
                        await _patient(conn, pair[side]) is not None
                    ), f"{pair['technique']} {side} missing"

            dup = dups[0]
            da = await _patient(conn, dup["patient_id_a"])
            db_ = await _patient(conn, dup["patient_id_b"])
            miss = misses[0]
            ma = await _patient(conn, miss["patient_id_a"])
            mb = await _patient(conn, miss["patient_id_b"])
    finally:
        await engine.dispose()

    assert da is not None and db_ is not None and ma is not None and mb is not None
    # a duplicate pair shares at least one identifier (name, dob or phone)...
    assert (
        da["phone"] == db_["phone"]
        or da["date_of_birth"] == db_["date_of_birth"]
        or set(str(da["full_name"]).split()) == set(str(db_["full_name"]).split())
    )
    # ...a near-miss pair shares a surname but is a different person.
    assert str(ma["full_name"]).split()[-1] == str(mb["full_name"]).split()[-1]
    assert ma["full_name"] != mb["full_name"]
