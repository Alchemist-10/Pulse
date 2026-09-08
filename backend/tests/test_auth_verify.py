"""Email verification: invalid token, replayed (expired) token, happy path.

The happy path is proven by a permissioned route flipping from
403 EMAIL_NOT_VERIFIED to 200 once verification completes.
"""

from collections.abc import AsyncIterator

import pytest_asyncio
from helpers import RegisterAndLogin, wipe_identity
from httpx import AsyncClient

from app.adapters.identity import FakeIdentityProvider

_PW = "correct-horse-staple-9"


@pytest_asyncio.fixture(autouse=True)
async def _isolate(app_database_url: str) -> AsyncIterator[None]:
    yield
    await wipe_identity(app_database_url)


async def _register(client: AsyncClient, email: str) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": _PW, "role": "PATIENT"},
    )
    reg.raise_for_status()


async def test_verify_invalid_challenge_is_422(
    client: AsyncClient, fake_idp: FakeIdentityProvider
) -> None:
    await _register(client, "v-invalid@example.com")
    resp = await client.post(
        "/api/v1/auth/verify",
        json={"challengeId": "not-a-real-challenge", "token": "nope"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VERIFICATION_TOKEN_INVALID"


async def test_verify_replayed_challenge_is_expired(
    client: AsyncClient, fake_idp: FakeIdentityProvider
) -> None:
    await _register(client, "v-replay@example.com")
    challenge_id, (token, _uid) = next(reversed(fake_idp.issued.items()))

    ok = await client.post(
        "/api/v1/auth/verify",
        json={"challengeId": challenge_id, "token": token},
    )
    assert ok.status_code == 200

    again = await client.post(
        "/api/v1/auth/verify",
        json={"challengeId": challenge_id, "token": token},
    )
    assert again.status_code == 422
    assert again.json()["error"]["code"] == "VERIFICATION_TOKEN_EXPIRED"


async def test_verify_unlocks_permissioned_routes(
    client: AsyncClient,
    register_and_login: RegisterAndLogin,
    fake_idp: FakeIdentityProvider,
) -> None:
    await register_and_login(email="v-happy@example.com", verify=False)
    blocked = await client.get("/api/v1/patients/me")
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"

    challenge_id, (token, _uid) = next(reversed(fake_idp.issued.items()))
    done = await client.post(
        "/api/v1/auth/verify",
        json={"challengeId": challenge_id, "token": token},
    )
    assert done.status_code == 200

    assert (await client.get("/api/v1/patients/me")).status_code == 200


async def test_resend_verification_never_reveals_existence(client: AsyncClient) -> None:
    known = await client.post(
        "/api/v1/auth/register",
        json={"email": "resend@example.com", "password": _PW, "role": "PATIENT"},
    )
    known.raise_for_status()

    for email in ("resend@example.com", "ghost@example.com"):
        resp = await client.post("/api/v1/auth/verify/resend", json={"email": email})
        assert resp.status_code == 202
