"""Users HTTP surface: a Patient persisting their interface locale.

Negatives first: unauthenticated is 401, a non-Patient is 403, and a locale
outside the four supported ones is a coded 422.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from helpers import RegisterAndLogin, wipe_identity
from httpx import AsyncClient


@pytest_asyncio.fixture(autouse=True)
async def _isolate(app_database_url: str) -> AsyncIterator[None]:
    yield
    await wipe_identity(app_database_url)


async def test_unauthenticated_is_401(client: AsyncClient) -> None:
    resp = await client.put("/api/v1/users/me/locale", json={"locale": "ta"})
    assert resp.status_code == 401


async def test_clinician_is_403(client: AsyncClient, register_and_login: RegisterAndLogin) -> None:
    await register_and_login(email="locale-dr@example.com", role="CLINICIAN")
    resp = await client.put("/api/v1/users/me/locale", json={"locale": "ta"})
    assert resp.status_code == 403


async def test_unsupported_locale_is_422(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="locale-bad@example.com")
    resp = await client.put("/api/v1/users/me/locale", json={"locale": "fr"})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_patient_locale_is_persisted(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="locale-ok@example.com")
    resp = await client.put("/api/v1/users/me/locale", json={"locale": "ml"})
    assert resp.status_code == 204
    assert (await client.get("/api/v1/patients/me")).json()["localePreference"] == "ml"
