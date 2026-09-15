"""Clinician lookup by email for the Consent grant form.

A Patient cannot know a clinician's user id, so the grant form resolves an
exact email to one. Negatives first: a non-clinician email and an unknown
email read identically (404), and a non-Patient cannot use the lookup.
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


async def test_unknown_and_non_clinician_emails_are_the_same_404(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="other-patient@example.com")
    await register_and_login(email="lookup-patient@example.com")

    unknown = await client.get("/api/v1/clinicians/lookup", params={"email": "nobody@example.com"})
    patient = await client.get(
        "/api/v1/clinicians/lookup", params={"email": "other-patient@example.com"}
    )
    assert unknown.status_code == patient.status_code == 404
    assert unknown.json()["error"]["code"] == patient.json()["error"]["code"]


async def test_clinician_cannot_use_lookup(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="lookup-dr@example.com", role="CLINICIAN")
    resp = await client.get("/api/v1/clinicians/lookup", params={"email": "lookup-dr@example.com"})
    assert resp.status_code == 403


async def test_patient_resolves_clinician_email_case_insensitively(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="lookup-dr2@example.com", role="CLINICIAN")
    me = (await client.get("/api/v1/auth/me")).json()
    await register_and_login(email="lookup-patient2@example.com")

    resp = await client.get(
        "/api/v1/clinicians/lookup", params={"email": "  Lookup-DR2@example.com "}
    )
    assert resp.status_code == 200
    assert resp.json() == {"userId": me["userId"], "email": "lookup-dr2@example.com"}
