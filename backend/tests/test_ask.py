"""Ask-your-record: rule-based chat over the patient's own record.

Negative first: unauthenticated, administrator, other patient's data and
audit-content leaks are checked before any positive answer, because a
positive test passes just as happily when the filter was never applied.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
import pytest_asyncio
import records_helpers as rh
from helpers import RegisterAndLogin, wipe_identity
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.modules.ask.intents import AskIntent, match_entity, match_intent


@pytest_asyncio.fixture(autouse=True)
async def _isolate(app_database_url: str) -> AsyncIterator[None]:
    yield
    await rh.wipe_records(app_database_url)
    await wipe_identity(app_database_url)


async def _ask(client: AsyncClient, question: str, **extra: Any) -> dict[str, Any]:
    resp = await client.post("/api/v1/ask", json={"question": question, **extra})
    assert resp.status_code == 200, resp.text
    return dict(resp.json())


async def _pid(client: AsyncClient) -> UUID:
    return UUID(str((await client.get("/api/v1/patients/me")).json()["id"]))


async def _lab(
    url: str, pid: UUID, *, days_ago: int, value: float, name: str = "Hemoglobin A1c"
) -> UUID:
    when = datetime.now(UTC) - timedelta(days=days_ago)
    return await rh.insert_entry(
        url,
        patient_id=pid,
        occurred_at=when,
        entry_type="LAB_REPORT",
        display_name=name,
        value_numeric=value,
    )


# --- negative first ---------------------------------------------------------


async def test_requires_login(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/ask", json={"question": "my medications"})
    assert resp.status_code == 401


async def test_administrator_gets_no_answer(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="ask-admin@example.com", role="ADMINISTRATOR")
    resp = await client.post("/api/v1/ask", json={"question": "my latest hba1c"})
    assert resp.status_code in (403, 404)


async def test_clinician_gets_no_answer(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="ask-doc@example.com", role="CLINICIAN")
    resp = await client.post("/api/v1/ask", json={"question": "my latest hba1c"})
    assert resp.status_code in (403, 404)


async def test_never_answers_from_another_patients_record(
    client: AsyncClient, register_and_login: RegisterAndLogin, app_database_url: str
) -> None:
    await register_and_login(email="ask-owner@example.com")
    await _lab(app_database_url, await _pid(client), days_ago=1, value=9.9)
    await client.post("/api/v1/auth/logout")
    await register_and_login(email="ask-stranger@example.com")
    body = await _ask(client, "what is my latest hba1c")
    assert body["blocks"][0]["kind"] == "message"
    assert "9.9" not in str(body)


async def test_audit_event_carries_intent_only(
    client: AsyncClient, register_and_login: RegisterAndLogin, app_database_url: str
) -> None:
    await register_and_login(email="ask-audit@example.com")
    pid = await _pid(client)
    await _lab(app_database_url, pid, days_ago=1, value=8.1)
    await _ask(client, "what is my latest hba1c")
    engine = create_async_engine(app_database_url)
    try:
        async with engine.connect() as conn:
            rows = (
                await conn.execute(
                    text(
                        "SELECT metadata::text FROM audit_event "
                        "WHERE resource_type = 'ask' AND patient_id = :pid"
                    ),
                    {"pid": pid},
                )
            ).all()
    finally:
        await engine.dispose()
    assert len(rows) == 1
    meta = rows[0][0]
    assert "LATEST_LAB" in meta
    assert "hba1c" not in meta.lower()
    assert "Hemoglobin" not in meta
    assert "8.1" not in meta


# --- positive ---------------------------------------------------------------


async def test_latest_lab_flags_abnormal(
    client: AsyncClient, register_and_login: RegisterAndLogin, app_database_url: str
) -> None:
    await register_and_login(email="ask-lab@example.com")
    pid = await _pid(client)
    await _lab(app_database_url, pid, days_ago=60, value=5.0)
    await _lab(app_database_url, pid, days_ago=2, value=7.8)
    body = await _ask(client, "what is my latest HbA1c?")
    block = body["blocks"][0]
    assert body["intent"] == "LATEST_LAB"
    assert block["kind"] == "lab_value"
    assert block["testName"] == "Hemoglobin A1c"
    assert float(block["valueNumeric"]) == 7.8
    assert block["isAbnormal"] is True
    assert body["receipt"]["filter"] == "accessible_entries"
    assert body["receipt"]["entryCount"] == 2


async def test_lab_trend_returns_points(
    client: AsyncClient, register_and_login: RegisterAndLogin, app_database_url: str
) -> None:
    await register_and_login(email="ask-trend@example.com")
    pid = await _pid(client)
    for d, v in ((90, 5.1), (45, 6.0), (3, 7.2)):
        await _lab(app_database_url, pid, days_ago=d, value=v)
    body = await _ask(client, "is my hba1c trend going up")
    block = body["blocks"][0]
    assert block["kind"] == "lab_trend"
    assert [p["isAbnormal"] for p in block["points"]] == [False, True, True]


async def test_unknown_test_lists_known_ones(
    client: AsyncClient, register_and_login: RegisterAndLogin, app_database_url: str
) -> None:
    await register_and_login(email="ask-unk@example.com")
    await _lab(app_database_url, await _pid(client), days_ago=1, value=5.0)
    body = await _ask(client, "what is my latest ferritin")
    assert body["blocks"][0]["key"] == "ask.lab.unknown_test"
    assert "Hemoglobin A1c" in body["blocks"][0]["params"]["tests"]


async def test_what_changed_lists_recent_entries(
    client: AsyncClient, register_and_login: RegisterAndLogin, app_database_url: str
) -> None:
    await register_and_login(email="ask-chg@example.com")
    pid = await _pid(client)
    await _lab(app_database_url, pid, days_ago=2, value=5.0)
    await _lab(app_database_url, pid, days_ago=200, value=5.0, name="Old Test")
    body = await _ask(client, "what changed in the last 7 days")
    block = body["blocks"][0]
    assert block["kind"] == "changes"
    assert len(block["added"]) == 1


async def test_who_accessed_hides_own_events(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="ask-who@example.com")
    await _ask(client, "my medications")  # patient's own activity must not appear
    body = await _ask(client, "who viewed my records this month")
    assert body["intent"] == "WHO_ACCESSED"
    assert body["blocks"][0]["key"] == "ask.access.none"


async def test_emergency_preview_not_set_up(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="ask-em@example.com")
    body = await _ask(client, "what would a paramedic see")
    assert body["blocks"][0] == {"kind": "emergency_preview", "card": None}


async def test_emergency_preview_respects_visibility(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="ask-em2@example.com")
    await client.put(
        "/api/v1/emergency-card",
        json={"bloodType": "O+", "notes": "private", "showBloodType": True, "showNotes": False},
    )
    card = (await _ask(client, "what would a paramedic see"))["blocks"][0]["card"]
    assert card["bloodType"] == "O+"
    assert card["notes"] is None


async def test_allergies_read_from_emergency_card(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="ask-all@example.com")
    assert (await _ask(client, "any allergies?"))["blocks"][0]["key"] == "ask.allergies.none"
    await client.put("/api/v1/emergency-card", json={"allergies": "Penicillin"})
    block = (await _ask(client, "any allergies?"))["blocks"][0]
    assert block["items"][0]["displayName"] == "Penicillin"


async def test_unmatched_offers_suggestions_and_logs_nothing(
    client: AsyncClient, register_and_login: RegisterAndLogin
) -> None:
    await register_and_login(email="ask-un@example.com")
    body = await _ask(client, "tell me a joke")
    assert body["intent"] == "UNMATCHED"
    assert body["blocks"][1]["kind"] == "suggestions"
    assert body["receipt"]["auditLogged"] is False


# --- matcher (pure) ---------------------------------------------------------


@pytest.mark.parametrize(
    ("question", "locale", "expected"),
    [
        ("who has seen my records", "en", AskIntent.WHO_ACCESSED),
        ("किसने मेरा रिकॉर्ड देखा", "hi", AskIntent.WHO_ACCESSED),
        ("யார் என் பதிவை பார்த்தார்", "ta", AskIntent.WHO_ACCESSED),
        ("ആരാണ് കണ്ടത്", "ml", AskIntent.WHO_ACCESSED),
        ("मेरी दवाइयां क्या हैं", "hi", AskIntent.MEDICATIONS),
        ("என் மருந்துகள் என்ன", "ta", AskIntent.MEDICATIONS),
        ("എന്റെ മരുന്നുകൾ", "ml", AskIntent.MEDICATIONS),
        ("एलर्जी", "hi", AskIntent.ALLERGIES),
        ("what changed since last visit", "en", AskIntent.WHAT_CHANGED),
        ("any allergys", "en", AskIntent.ALLERGIES),
        ("what is the weather", "en", AskIntent.UNMATCHED),
    ],
)
def test_intent_per_locale(question: str, locale: str, expected: AskIntent) -> None:
    assert match_intent(question, locale).intent is expected  # type: ignore[arg-type]


def test_window_parsing() -> None:
    assert match_intent("who viewed my records this week", "en").window_days == 7
    assert match_intent("who viewed my records in 3 months", "en").window_days == 90
    assert match_intent("who viewed my records", "en").window_days is None


def test_entity_match_containment() -> None:
    names = ["Hemoglobin A1c", "Total Cholesterol", "Glucose"]
    assert match_entity(names, "my latest hba1c") == "Hemoglobin A1c"
    assert match_entity(names, "my cholesterol") == "Total Cholesterol"
    assert match_entity(names, "my ferritin") is None
