"""Login: generic failure (no email enumeration), cookie attributes."""

from collections.abc import AsyncIterator

import pytest_asyncio
from helpers import wipe_identity
from httpx import AsyncClient

from app.adapters.identity import FakeIdentityProvider

_PW = "correct-horse-staple-9"


@pytest_asyncio.fixture(autouse=True)
async def _isolate(app_database_url: str) -> AsyncIterator[None]:
    yield
    await wipe_identity(app_database_url)


async def _register_verified(
    client: AsyncClient, fake_idp: FakeIdentityProvider, email: str
) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": _PW, "role": "PATIENT"},
    )
    reg.raise_for_status()
    challenge_id, (token, _uid) = next(reversed(fake_idp.issued.items()))
    v = await client.post(
        "/api/v1/auth/verify",
        json={"challengeId": challenge_id, "token": token},
    )
    v.raise_for_status()


async def test_login_wrong_password_and_unknown_email_are_identical(
    client: AsyncClient, fake_idp: FakeIdentityProvider
) -> None:
    await _register_verified(client, fake_idp, "login-neg@example.com")

    wrong_pw = await client.post(
        "/api/v1/auth/login",
        json={"email": "login-neg@example.com", "password": "not-the-password"},
    )
    unknown = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": _PW},
    )

    assert wrong_pw.status_code == unknown.status_code == 401
    assert (
        wrong_pw.json()["error"]["code"]
        == unknown.json()["error"]["code"]
        == "INVALID_CREDENTIALS"
    )
    assert wrong_pw.json()["error"]["message"] == unknown.json()["error"]["message"]
    assert "set-cookie" not in wrong_pw.headers


async def test_login_success_sets_hardened_session_cookie(
    client: AsyncClient, fake_idp: FakeIdentityProvider
) -> None:
    await _register_verified(client, fake_idp, "login-ok@example.com")
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login-ok@example.com", "password": _PW},
    )
    assert resp.status_code == 200
    raw = resp.headers["set-cookie"].lower()
    assert "pulse_session=" in raw
    assert "httponly" in raw
    assert "samesite=lax" in raw
    assert "path=/" in raw
    # No Max-Age: a session cookie, real lifetime is the Redis record
    # (sliding 60m idle / 12h cap, ADR-0003).
    assert "max-age" not in raw
    assert "expires" not in raw
    assert "secure" not in raw


async def test_unverified_user_can_still_login(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "unverified@example.com", "password": _PW, "role": "PATIENT"},
    )
    reg.raise_for_status()
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "unverified@example.com", "password": _PW},
    )
    assert resp.status_code == 200
