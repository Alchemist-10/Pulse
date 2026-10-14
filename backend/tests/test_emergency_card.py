"""Emergency card (ADR-0017): patient-controlled, QR/break-glass only.

Negative first: unauthenticated, rotated, disabled, admin and ungranted
reads all fail before the positive path is exercised.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from helpers import RegisterAndLogin, wipe_identity
from httpx import AsyncClient

_CARD = {
    "bloodType": "O+",
    "allergies": "Penicillin",
    "conditions": "Asthma",
    "medications": "Salbutamol",
    "nextOfKinName": "Asha Rao",
    "nextOfKinPhone": "9000000000",
    "nextOfKinRelation": "Spouse",
    "notes": "Private note",
    "showBloodType": True,
    "showAllergies": True,
    "showConditions": False,
    "showMedications": True,
    "showNextOfKin": True,
    "showNotes": False,
}


@pytest_asyncio.fixture(autouse=True)
async def _isolate(app_database_url: str) -> AsyncIterator[None]:
    yield
    await wipe_identity(app_database_url)


async def _patient_with_qr(
    client: AsyncClient, register_and_login: RegisterAndLogin, email: str
) -> str:
    await register_and_login(email=email)
    assert (await client.put("/api/v1/emergency-card", json=_CARD)).status_code == 200
    qr = await client.post("/api/v1/emergency-card/qr")
    assert qr.status_code == 200
    return str(qr.json()["qrToken"])


async def test_scan_requires_login(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/emergency-card/by-token/whatever")
    assert resp.status_code == 401


async def test_unknown_token_is_404(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="ec-unknown@example.com", role="CLINICIAN")
    resp = await client.get("/api/v1/emergency-card/by-token/nope")
    assert resp.status_code == 404


async def test_hidden_fields_never_leave_the_server(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    token = await _patient_with_qr(client, register_and_login, "ec-p1@example.com")
    await register_and_login(email="ec-c1@example.com", role="CLINICIAN")
    resp = await client.get(f"/api/v1/emergency-card/by-token/{token}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["bloodType"] == "O+"
    assert body["allergies"] == "Penicillin"
    assert body["conditions"] is None
    assert body["notes"] is None


async def test_scan_is_audited_and_notified(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    token = await _patient_with_qr(client, register_and_login, "ec-p2@example.com")
    pid = (await client.get("/api/v1/patients/me")).json()["id"]
    await register_and_login(email="ec-c2@example.com", role="CLINICIAN")
    assert (await client.get(f"/api/v1/emergency-card/by-token/{token}")).status_code == 200

    await register_and_login(email="ec-p2@example.com")
    events = await client.get("/api/v1/audit-events", params={"patientId": pid})
    assert "EMERGENCY_CARD_VIEWED" in [e["action"] for e in events.json()["items"]]
    notes = await client.get("/api/v1/notifications")
    assert "EMERGENCY_CARD_VIEWED" in [n["type"] for n in notes.json()["items"]]


async def test_rotated_and_disabled_tokens_stop_working(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    old = await _patient_with_qr(client, register_and_login, "ec-p3@example.com")
    new = (await client.post("/api/v1/emergency-card/qr")).json()["qrToken"]
    assert new != old
    await register_and_login(email="ec-c3@example.com", role="CLINICIAN")
    assert (await client.get(f"/api/v1/emergency-card/by-token/{old}")).status_code == 404
    assert (await client.get(f"/api/v1/emergency-card/by-token/{new}")).status_code == 200

    await register_and_login(email="ec-p3@example.com")
    assert (await client.delete("/api/v1/emergency-card/qr")).status_code == 200
    await register_and_login(email="ec-c3@example.com")
    assert (await client.get(f"/api/v1/emergency-card/by-token/{new}")).status_code == 404


async def test_administrator_cannot_view_cards(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    token = await _patient_with_qr(client, register_and_login, "ec-p4@example.com")
    await register_and_login(email="ec-a4@example.com", role="ADMINISTRATOR")
    resp = await client.get(f"/api/v1/emergency-card/by-token/{token}")
    assert resp.status_code == 403


async def test_clinician_without_grant_gets_404_by_patient_id(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="ec-p5@example.com")
    pid = (await client.get("/api/v1/patients/me")).json()["id"]
    await register_and_login(email="ec-c5@example.com", role="CLINICIAN")
    assert (await client.get(f"/api/v1/patients/{pid}/emergency-card")).status_code == 404


async def test_mark_all_read_clears_unread(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    token = await _patient_with_qr(client, register_and_login, "ec-p6@example.com")
    await register_and_login(email="ec-c6@example.com", role="CLINICIAN")
    await client.get(f"/api/v1/emergency-card/by-token/{token}")
    await register_and_login(email="ec-p6@example.com")
    resp = await client.post("/api/v1/notifications/read-all")
    assert resp.status_code == 200
    assert resp.json()["updated"] >= 1
    items = (await client.get("/api/v1/notifications")).json()["items"]
    assert all(n["readAt"] is not None for n in items)
    assert (await client.post("/api/v1/notifications/read-all")).json()["updated"] == 0
