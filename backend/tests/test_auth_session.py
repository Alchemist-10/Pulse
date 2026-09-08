"""Session lifecycle: 401 without a cookie, logout, logout-everywhere, /auth/me."""

from collections.abc import AsyncIterator

import pytest_asyncio
from helpers import RegisterAndLogin, wipe_identity
from httpx import AsyncClient

from app.core.redis import get_redis
from app.core.sessions import read_session

_PW = "correct-horse-staple-9"


@pytest_asyncio.fixture(autouse=True)
async def _isolate(app_database_url: str) -> AsyncIterator[None]:
    yield
    await wipe_identity(app_database_url)


async def test_me_without_cookie_is_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] in {"UNAUTHORIZED", "SESSION_EXPIRED"}


async def test_unverified_user_can_read_own_state_and_log_out(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    """The session-management routes pass verified=False. An unverified user
    holds a valid session and must be able to see it is unverified and end it —
    withdrawing access is the frictionless direction (backend.md)."""
    await register_and_login(email="unverified-session@example.com", verify=False)

    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["emailVerified"] is False

    out = await client.post("/api/v1/auth/logout")
    assert out.status_code == 204
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_logout_destroys_the_current_session(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="logout@example.com")
    assert (await client.get("/api/v1/auth/me")).status_code == 200

    out = await client.post("/api/v1/auth/logout")
    assert out.status_code == 204

    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_logout_all_kills_every_session_for_the_user(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="logoutall@example.com")
    token_one = client.cookies["pulse_session"]

    second = await client.post(
        "/api/v1/auth/login",
        json={"email": "logoutall@example.com", "password": _PW},
    )
    second.raise_for_status()
    token_two = client.cookies["pulse_session"]
    assert token_one != token_two

    killed = await client.post("/api/v1/auth/logout-all")
    assert killed.status_code == 204

    redis = get_redis()
    assert await read_session(redis, token_one) is None
    assert await read_session(redis, token_two) is None

    client.cookies.set("pulse_session", token_one)
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_me_returns_the_signed_in_identity(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="whoami@example.com", role="CLINICIAN")
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "whoami@example.com"
    assert body["role"] == "CLINICIAN"
    assert body["emailVerified"] is True
    assert body["userId"]
