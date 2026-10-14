"""Admin directory: identity + counts only, Administrator only (ADR-0007)."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from helpers import RegisterAndLogin, wipe_identity
from httpx import AsyncClient


@pytest_asyncio.fixture(autouse=True)
async def _isolate(app_database_url: str) -> AsyncIterator[None]:
    yield
    await wipe_identity(app_database_url)


async def test_non_admin_forbidden(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="dir-p@example.com")
    pid = (await client.get("/api/v1/patients/me")).json()["id"]
    for path in (
        "/api/v1/admin/summary",
        "/api/v1/admin/patients",
        f"/api/v1/admin/patients/{pid}",
        "/api/v1/admin/users",
    ):
        assert (await client.get(path)).status_code == 403


async def test_admin_sees_identity_and_counts_only(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="dir-p2@example.com")
    pid = (await client.get("/api/v1/patients/me")).json()["id"]
    await register_and_login(email="dir-a@example.com", role="ADMINISTRATOR")

    summary = (await client.get("/api/v1/admin/summary")).json()
    assert summary["patients"] >= 1

    rows = (await client.get("/api/v1/admin/patients", params={"limit": 100})).json()["items"]
    assert pid in [r["id"] for r in rows]

    detail = (await client.get(f"/api/v1/admin/patients/{pid}")).json()
    assert detail["entryCount"] == 0
    assert {"activeConsentCount", "totalConsentCount", "auditEventCount"} <= detail.keys()
    assert not {"entries", "diagnoses", "allergies"} & detail.keys()

    users = (await client.get("/api/v1/admin/users", params={"role": "PATIENT"})).json()["items"]
    assert all(u["role"] == "PATIENT" for u in users)
    missing = await client.get("/api/v1/admin/patients/00000000-0000-0000-0000-000000000000")
    assert missing.status_code == 404
