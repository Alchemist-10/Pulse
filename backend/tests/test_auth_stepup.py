"""Step-up: wrong password is rejected and grants nothing; right password
opens a short window. No Phase 1 route consumes `requires_step_up` yet, so
the window is asserted directly via the session store.
"""

from collections.abc import AsyncIterator

import pytest_asyncio
from helpers import RegisterAndLogin, wipe_identity
from httpx import AsyncClient

from app.core.redis import get_redis
from app.core.sessions import has_step_up

_PW = "correct-horse-staple-9"


@pytest_asyncio.fixture(autouse=True)
async def _isolate(app_database_url: str) -> AsyncIterator[None]:
    yield
    await wipe_identity(app_database_url)


async def test_step_up_wrong_password_rejected_and_grants_nothing(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="stepup-neg@example.com")
    token = client.cookies["pulse_session"]

    resp = await client.post("/api/v1/auth/step-up", json={"password": "wrong-password"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert await has_step_up(get_redis(), token) is False


async def test_step_up_correct_password_opens_window(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="stepup-ok@example.com")
    token = client.cookies["pulse_session"]

    resp = await client.post("/api/v1/auth/step-up", json={"password": _PW})
    assert resp.status_code == 200
    assert resp.json() == {}
    assert await has_step_up(get_redis(), token) is True


async def test_step_up_requires_authentication(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/step-up", json={"password": _PW})
    assert resp.status_code == 401
