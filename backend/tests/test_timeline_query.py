"""P2.3 — cursor-paginated, polymorphic, superseded-filtered timeline read.

ASGI-client seam (exercises P2.3 + P2.5 together). Entries are seeded with raw
SQL; assertions are all on the HTTP response. Written red: neither the tables
nor ``GET /patients/{id}/entries`` exist yet.

Negative tests first — a superseded entry absent, pages that never overlap —
because each passes just as happily when the filter was never written.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest_asyncio
import records_helpers as rh
from helpers import RegisterAndLogin, wipe_identity
from httpx import AsyncClient

_PW = "correct-horse-staple-9"


@pytest_asyncio.fixture(autouse=True)
async def _isolate(app_database_url: str) -> AsyncIterator[None]:
    yield
    await rh.wipe_records(app_database_url)
    await wipe_identity(app_database_url)


async def _patient_id(client: AsyncClient) -> UUID:
    resp = await client.get("/api/v1/patients/me")
    resp.raise_for_status()
    return UUID(str(resp.json()["id"]))


async def test_timeline_orders_by_occurred_at_desc(
    client: AsyncClient, register_and_login: RegisterAndLogin, app_database_url: str
) -> None:
    await register_and_login(email="tl-order@example.com")
    pid = await _patient_id(client)
    base = datetime(2025, 1, 1, tzinfo=UTC)
    for days in (0, 30, 10):
        await rh.insert_entry(
            app_database_url,
            patient_id=pid,
            occurred_at=base + timedelta(days=days),
            recorded_at=base + timedelta(days=90),
        )

    resp = await client.get(f"/api/v1/patients/{pid}/entries")
    assert resp.status_code == 200
    occurred = [item["occurredAt"] for item in resp.json()["items"]]
    assert occurred == sorted(occurred, reverse=True)


async def test_superseded_entry_is_absent_but_reachable_by_id(
    client: AsyncClient, register_and_login: RegisterAndLogin, app_database_url: str
) -> None:
    await register_and_login(email="tl-supersede@example.com")
    pid = await _patient_id(client)
    now = datetime(2025, 6, 1, tzinfo=UTC)
    correction = await rh.insert_entry(
        app_database_url,
        patient_id=pid,
        occurred_at=now,
    )
    original = await rh.insert_entry(
        app_database_url,
        patient_id=pid,
        occurred_at=now,
        superseded_by_id=correction,
    )

    listing = await client.get(f"/api/v1/patients/{pid}/entries")
    assert listing.status_code == 200
    ids = {item["id"] for item in listing.json()["items"]}
    assert str(original) not in ids
    assert str(correction) in ids

    detail = await client.get(f"/api/v1/entries/{original}")
    assert detail.status_code == 200
    assert detail.json()["supersededById"] == str(correction)


async def test_cursor_pages_do_not_overlap_or_skip(
    client: AsyncClient, register_and_login: RegisterAndLogin, app_database_url: str
) -> None:
    await register_and_login(email="tl-cursor@example.com")
    pid = await _patient_id(client)
    base = datetime(2025, 1, 1, tzinfo=UTC)
    for i in range(5):
        await rh.insert_entry(
            app_database_url,
            patient_id=pid,
            occurred_at=base + timedelta(days=i),
        )

    first = await client.get(f"/api/v1/patients/{pid}/entries?limit=2")
    assert first.status_code == 200
    body = first.json()
    assert len(body["items"]) == 2
    assert body["nextCursor"]

    # An insert between pages must not shift the window.
    await rh.insert_entry(
        app_database_url,
        patient_id=pid,
        occurred_at=base + timedelta(days=10),
    )

    second = await client.get(
        f"/api/v1/patients/{pid}/entries?limit=2&cursor={body['nextCursor']}"
    )
    assert second.status_code == 200
    page1 = {i["id"] for i in body["items"]}
    page2 = {i["id"] for i in second.json()["items"]}
    assert page1.isdisjoint(page2)


async def test_entry_type_filter_narrows_the_timeline(
    client: AsyncClient, register_and_login: RegisterAndLogin, app_database_url: str
) -> None:
    await register_and_login(email="tl-filter@example.com")
    pid = await _patient_id(client)
    now = datetime(2025, 3, 1, tzinfo=UTC)
    await rh.insert_entry(
        app_database_url,
        patient_id=pid,
        occurred_at=now,
        entry_type="CLINICAL_NOTE",
    )
    await rh.insert_entry(
        app_database_url,
        patient_id=pid,
        occurred_at=now,
        entry_type="LAB_REPORT",
    )

    resp = await client.get(
        f"/api/v1/patients/{pid}/entries?entryType=LAB_REPORT"
    )
    assert resp.status_code == 200
    kinds = {item["entryType"] for item in resp.json()["items"]}
    assert kinds == {"LAB_REPORT"}


async def test_a_malformed_cursor_is_a_coded_400_not_a_500(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="tl-badcursor@example.com")
    pid = await _patient_id(client)
    # Valid base64, nonsense payload — must not reach an uncaught fromisoformat.
    resp = await client.get(f"/api/v1/patients/{pid}/entries?cursor=eHl6")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
