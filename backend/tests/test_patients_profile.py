"""Patient profile: 401 without a cookie, 403 for a non-Patient Role,
the real /patients/me row, the 404 branch, and /patients/{id} access —
the real consent-aware resolution, not the G2 stub it replaced (#56).
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest_asyncio
import records_helpers as rh
from helpers import RegisterAndLogin, identity_session, wipe_identity
from httpx import AsyncClient
from sqlalchemy import delete

from app.adapters.notifications import FakeNotificationProvider
from app.main import app
from app.modules.consent.dependencies import get_notification_provider
from app.modules.users.models import Patient

_PW = "correct-horse-staple-9"


@pytest_asyncio.fixture(autouse=True)
async def _isolate(app_database_url: str) -> AsyncIterator[None]:
    yield
    await wipe_identity(app_database_url)


@pytest_asyncio.fixture(autouse=True)
async def _fake_notifications() -> AsyncIterator[None]:
    """Revocation notifies the Patient through the real SMTP adapter;
    this file has no Mailpit. Same swap the adversarial suite uses."""
    app.dependency_overrides[get_notification_provider] = FakeNotificationProvider
    yield
    app.dependency_overrides.pop(get_notification_provider, None)


async def test_patients_me_without_cookie_is_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/patients/me")
    assert resp.status_code == 401


async def test_clinician_is_forbidden_from_patient_profile(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="clin@example.com", role="CLINICIAN")
    resp = await client.get("/api/v1/patients/me")
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


async def test_patient_reads_own_profile(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="owner@example.com")
    resp = await client.get("/api/v1/patients/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["fullName"] == "owner"
    assert body["claimed"] is True
    assert body["localePreference"] == "en"


async def test_patient_by_id_denies_an_unrelated_clinician_with_404(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    """Negative first (backend.md): a Clinician with no Consent for this
    Patient gets 404, never a 403 that would confirm the Patient exists
    (clinical-safety.md). An Administrator resolves no access either
    (ADR-0007) — same 404."""
    await register_and_login(email="id-clin@example.com", role="CLINICIAN")
    resp = await client.get(f"/api/v1/patients/{uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


async def test_patient_by_id_serves_owner_and_consented_clinician(
    client: AsyncClient,
    register_and_login: RegisterAndLogin,
    app_database_url: str,
) -> None:
    """Positive path, granted through the real consent API end to end:
    the owner reads their own row by id, and so does a Clinician holding a
    live Consent for them — then 404s again the moment it is revoked."""
    await register_and_login(email="id-owner@example.com")
    pid = (await client.get("/api/v1/patients/me")).json()["id"]

    own = await client.get(f"/api/v1/patients/{pid}")
    assert own.status_code == 200
    assert own.headers.get("x-pulse-stub") is None
    assert own.json()["id"] == pid

    await register_and_login(email="id-grantee@example.com", role="CLINICIAN")
    clin_id = str(await rh.user_id_for_email(app_database_url, "id-grantee@example.com"))

    await register_and_login(email="id-owner@example.com")
    await client.post("/api/v1/auth/step-up", json={"password": _PW})
    grant = await client.post(
        "/api/v1/consents",
        json={
            "granteeUserId": clin_id,
            "entryTypes": ["LAB_REPORT"],
            "purpose": "TREATMENT",
            "expiresAt": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
        },
    )
    assert grant.status_code == 200

    await register_and_login(email="id-grantee@example.com")
    allowed = await client.get(f"/api/v1/patients/{pid}")
    assert allowed.status_code == 200
    assert allowed.json()["id"] == pid

    await register_and_login(email="id-owner@example.com")
    consent_id = grant.json()["id"]
    revoked = await client.post(f"/api/v1/consents/{consent_id}/revocation", json={"reason": None})
    assert revoked.status_code == 200

    await register_and_login(email="id-grantee@example.com")
    after_revoke = await client.get(f"/api/v1/patients/{pid}")
    assert after_revoke.status_code == 404


async def test_patient_me_is_404_when_the_row_is_gone(
    client: AsyncClient, register_and_login: RegisterAndLogin, app_database_url: str
) -> None:
    await register_and_login(email="rowless@example.com")
    async with identity_session(app_database_url) as session:
        await session.execute(delete(Patient))
        await session.commit()

    resp = await client.get("/api/v1/patients/me")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"
