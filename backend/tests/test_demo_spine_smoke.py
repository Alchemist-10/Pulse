"""P2.11 — the demo spine: a Provider Staff user files a Lab Report with a
document, and the Patient sees it on their timeline.

This is the CI smoke test the delivery plan calls for — a break anywhere in
upload -> timeline fails a PR, not the rehearsal. It uses only real endpoints
(no raw-SQL seeding) so it exercises the whole create path. Written red until
P2.1 / P2.3 / P2.5 / P2.6 land.
"""

from __future__ import annotations

import importlib
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
import records_helpers as rh
from helpers import RegisterAndLogin, wipe_identity
from httpx import AsyncClient

_PW = "correct-horse-staple-9"
_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"

_LAB_ENTRY = {
    "entryType": "LAB_REPORT",
    "codeSystem": "http://loinc.org",
    "code": "4548-4",
    "displayName": "Hemoglobin A1c",
    "valueNumeric": 7.8,
    "unit": "%",
    "referenceLow": 4.0,
    "referenceHigh": 5.6,
    "occurredAt": "2025-04-01T00:00:00Z",
}


@pytest_asyncio.fixture(autouse=True)
async def _isolate(app_database_url: str) -> AsyncIterator[None]:
    yield
    await rh.wipe_records(app_database_url)
    await wipe_identity(app_database_url)


@pytest.fixture
def _storage_to_tmp(tmp_path: Path) -> Iterator[None]:
    try:
        deps = importlib.import_module("app.modules.records.dependencies")
        main = importlib.import_module("app.main")
    except ModuleNotFoundError:
        yield
        return
    hook = getattr(deps, "get_storage_provider", None)
    if hook is None:
        yield
        return

    class _TmpStorage:
        async def put(self, key: str, data: bytes, content_type: str) -> str:
            dest = tmp_path / key
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            return str(dest)

        async def get(self, path: str) -> bytes:
            return Path(path).read_bytes()

    main.app.dependency_overrides[hook] = lambda: _TmpStorage()
    yield
    main.app.dependency_overrides.pop(hook, None)


@pytest.mark.usefixtures("_storage_to_tmp")
async def test_upload_lands_on_the_patient_timeline(
    client: AsyncClient, register_and_login: RegisterAndLogin, app_database_url: str
) -> None:
    # 1. a Patient exists
    await register_and_login(email="spine-patient@example.com")
    pid = str((await client.get("/api/v1/patients/me")).json()["id"])

    # 2. a Provider Staff user files a Lab Report against them
    await register_and_login(email="spine-staff@example.com", role="PROVIDER_STAFF")
    await rh.seed_provider_staff(app_database_url, user_email="spine-staff@example.com")

    created = await client.post(f"/api/v1/patients/{pid}/entries", json=_LAB_ENTRY)
    assert created.status_code == 201
    entry_id = created.json()["id"]

    doc = await client.post(
        f"/api/v1/patients/{pid}/entries/{entry_id}/documents",
        files={"file": ("hba1c.pdf", _PDF, "application/pdf")},
    )
    assert doc.status_code == 201

    # 3. the Patient logs back in and sees it, with its document
    await register_and_login(email="spine-patient@example.com")
    timeline = await client.get(f"/api/v1/patients/{pid}/entries")
    assert timeline.status_code == 200
    items = timeline.json()["items"]
    assert [i["id"] for i in items] == [entry_id]

    detail = await client.get(f"/api/v1/entries/{entry_id}")
    assert detail.status_code == 200
    assert len(detail.json()["documents"]) == 1


@pytest.mark.usefixtures("_storage_to_tmp")
async def test_oversized_upload_is_rejected_end_to_end(
    client: AsyncClient, register_and_login: RegisterAndLogin, app_database_url: str
) -> None:
    await register_and_login(email="spine-patient2@example.com")
    pid = str((await client.get("/api/v1/patients/me")).json()["id"])
    await register_and_login(email="spine-staff2@example.com", role="PROVIDER_STAFF")
    await rh.seed_provider_staff(app_database_url, user_email="spine-staff2@example.com")
    entry_id = (await client.post(f"/api/v1/patients/{pid}/entries", json=_LAB_ENTRY)).json()["id"]

    huge = b"%PDF-1.4\n" + b"0" * (26 * 1024 * 1024)
    resp = await client.post(
        f"/api/v1/patients/{pid}/entries/{entry_id}/documents",
        files={"file": ("huge.pdf", huge, "application/pdf")},
    )
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
