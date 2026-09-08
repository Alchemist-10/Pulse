"""P2.5 (#30) — the providers module read surface.

`GET /api/v1/providers/{id}` returns a Provider's public identity to any
signed-in role; an unknown id is 404; no cookie is 401.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest_asyncio
import records_helpers as rh
from helpers import RegisterAndLogin, wipe_identity
from httpx import AsyncClient

from app.modules.providers.schemas import Provider


@pytest_asyncio.fixture(autouse=True)
async def _isolate(app_database_url: str) -> AsyncIterator[None]:
    yield
    await rh.wipe_records(app_database_url)
    await wipe_identity(app_database_url)


async def test_provider_by_id_is_public_identity(
    client: AsyncClient, register_and_login: RegisterAndLogin, app_database_url: str
) -> None:
    await register_and_login(email="prov-staff@example.com", role="PROVIDER_STAFF")
    provider_id = await rh.seed_provider_staff(
        app_database_url, user_email="prov-staff@example.com"
    )

    resp = await client.get(f"/api/v1/providers/{provider_id}")
    assert resp.status_code == 200
    provider = Provider.model_validate(resp.json())
    assert provider.id == provider_id
    assert provider.name == "Apollo Speciality Hospital"


async def test_unknown_provider_is_404(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="prov-reader@example.com")
    resp = await client.get(f"/api/v1/providers/{uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


async def test_provider_read_requires_auth(client: AsyncClient) -> None:
    resp = await client.get(f"/api/v1/providers/{uuid4()}")
    assert resp.status_code == 401
