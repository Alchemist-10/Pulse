"""P2.0 (#25) — the six records/consent/audit `@stub` endpoints.

One test per stub: authenticated request -> 200, `x-pulse-stub: true`,
body parses into the declared schema. Prior art:
`test_patients_profile.py::test_patient_by_id_is_a_stub`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest_asyncio
from helpers import RegisterAndLogin, wipe_identity
from httpx import AsyncClient

from app.core.pagination import Page
from app.modules.audit.schemas import AuditEventProjection
from app.modules.consent.schemas import Consent
from app.modules.records.schemas import EntryDetail, EntrySummary


@pytest_asyncio.fixture(autouse=True)
async def _isolate(app_database_url: str) -> AsyncIterator[None]:
    yield
    await wipe_identity(app_database_url)


async def _login(register_and_login: RegisterAndLogin, email: str) -> None:
    await register_and_login(email=email)


async def test_list_patient_entries_is_a_stub(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await _login(register_and_login, "entries-stub@example.com")
    resp = await client.get(f"/api/v1/patients/{uuid4()}/entries")
    assert resp.status_code == 200
    assert resp.headers["x-pulse-stub"] == "true"
    Page[EntrySummary].model_validate(resp.json())


async def test_entry_detail_is_a_stub(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await _login(register_and_login, "entry-detail-stub@example.com")
    resp = await client.get(f"/api/v1/entries/{uuid4()}")
    assert resp.status_code == 200
    assert resp.headers["x-pulse-stub"] == "true"
    EntryDetail.model_validate(resp.json())


async def test_list_consents_is_a_stub(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await _login(register_and_login, "consents-stub@example.com")
    resp = await client.get("/api/v1/consents", params={"patientId": str(uuid4())})
    assert resp.status_code == 200
    assert resp.headers["x-pulse-stub"] == "true"
    Page[Consent].model_validate(resp.json())


async def test_grant_consent_is_a_stub(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await _login(register_and_login, "grant-stub@example.com")
    resp = await client.post(
        "/api/v1/consents",
        json={
            "granteeUserId": str(uuid4()),
            "purpose": "TREATMENT",
            "expiresAt": "2025-12-31T00:00:00Z",
            "entryTypes": ["LAB_REPORT"],
        },
    )
    assert resp.status_code == 200
    assert resp.headers["x-pulse-stub"] == "true"
    Consent.model_validate(resp.json())


async def test_revoke_consent_is_a_stub(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await _login(register_and_login, "revoke-stub@example.com")
    resp = await client.post(
        f"/api/v1/consents/{uuid4()}/revocation", json={"reason": "No longer treating"}
    )
    assert resp.status_code == 200
    assert resp.headers["x-pulse-stub"] == "true"
    Consent.model_validate(resp.json())


async def test_list_audit_events_is_a_stub(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await _login(register_and_login, "audit-stub@example.com")
    resp = await client.get("/api/v1/audit-events", params={"patientId": str(uuid4())})
    assert resp.status_code == 200
    assert resp.headers["x-pulse-stub"] == "true"
    Page[AuditEventProjection].model_validate(resp.json())
