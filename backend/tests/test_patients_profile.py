"""Patient profile: 401 without a cookie, 403 for a non-Patient Role,
the real /patients/me row, the 404 branch, and the /patients/{id} stub header.
"""

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest_asyncio
from helpers import RegisterAndLogin, identity_session, wipe_identity
from httpx import AsyncClient
from sqlalchemy import delete

from app.modules.users.models import Patient

_PW = "correct-horse-staple-9"


@pytest_asyncio.fixture(autouse=True)
async def _isolate(app_database_url: str) -> AsyncIterator[None]:
    yield
    await wipe_identity(app_database_url)


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


async def test_patient_by_id_is_a_stub(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="stub-reader@example.com")
    resp = await client.get(f"/api/v1/patients/{uuid4()}")
    assert resp.status_code == 200
    assert resp.headers["x-pulse-stub"] == "true"


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
