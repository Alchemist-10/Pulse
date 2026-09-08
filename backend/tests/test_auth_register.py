"""Registration: validation, duplicate email, and the linked Patient row.

Negative first (backend.md): a positive register test passes just as
happily when the uniqueness check was never applied.
"""

from collections.abc import AsyncIterator

import pytest_asyncio
from helpers import identity_session, wipe_identity
from httpx import AsyncClient
from sqlalchemy import select

from app.modules.users.models import Patient, User

_PW = "correct-horse-staple-9"


@pytest_asyncio.fixture(autouse=True)
async def _isolate(app_database_url: str) -> AsyncIterator[None]:
    yield
    await wipe_identity(app_database_url)


async def test_register_rejects_short_password(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "shorty@example.com", "password": "abc", "role": "PATIENT"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["details"]


async def test_register_duplicate_email_conflicts(client: AsyncClient) -> None:
    first = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": _PW, "role": "PATIENT"},
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/auth/register",
        json={"email": "DUP@example.com", "password": _PW, "role": "CLINICIAN"},
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


async def test_register_patient_creates_linked_patient_row(
    client: AsyncClient, app_database_url: str
) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "newpatient@example.com", "password": _PW, "role": "PATIENT"},
    )
    assert resp.status_code == 201
    user_id = resp.json()["userId"]

    async with identity_session(app_database_url) as session:
        user = (
            await session.execute(
                select(User).where(User.email == "newpatient@example.com")
            )
        ).scalar_one()
        assert str(user.id) == user_id
        assert user.email_verified_at is None

        patient = (
            await session.execute(select(Patient).where(Patient.user_id == user.id))
        ).scalar_one()
        assert patient.full_name == "newpatient"


async def test_register_clinician_creates_no_patient_row(
    client: AsyncClient, app_database_url: str
) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "doc@example.com", "password": _PW, "role": "CLINICIAN"},
    )
    assert resp.status_code == 201
    user_id = resp.json()["userId"]

    async with identity_session(app_database_url) as session:
        linked = (
            await session.execute(
                select(Patient).where(Patient.user_id == user_id)
            )
        ).scalar_one_or_none()
        assert linked is None
