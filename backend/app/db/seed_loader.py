"""First-boot identity seed loader.

Invoked by the backend container entrypoint after ``alembic upgrade head``
and before ``uvicorn``. Loads the committed, deterministic dataset in
``seed/data/identity/`` -- Provider, ProviderStaff, User, Patient only.
Phase 1 has no clinical tables, so ``seed/data/clinical/`` is never read
here (it is staged for Phase 2).

Idempotent: a single ``seed_marker`` row (migration 0003) is written at
the end of a successful load. A second run finds it and returns without
touching a table, so a second ``docker compose up`` is a no-op.

The committed CSVs carry no password hashes -- argon2 output is
non-deterministic and would break the "regenerate -> git diff empty"
contract (ADR-0015). Instead, ``users.csv`` flags demo logins; this
loader stamps a hash of the public dev password and ``email_verified_at``
for those rows at load time. Every other seeded User shares one hash of a
random secret -- a NOT NULL value no password can satisfy. Argon2 runs
exactly twice per boot, not once per row.
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import os
import secrets
import uuid
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import Role
from app.core.security import hash_password
from app.db.session import async_session
from app.modules.users.models import Patient, Provider, ProviderKind, ProviderStaff, Sex, User

# Public demo credential -- this project never holds real patient data
# (clinical-safety.md). Mirrors seed/scripts/common.DEV_PASSWORD.
DEV_PASSWORD = "Pulse@demo1"  # documented public demo credential
VERIFIED_AT = datetime.fromisoformat("2026-01-01T00:00:00+00:00")

# Argon2 is deliberately slow; hash exactly twice per boot, not once per row.
# Every demo user shares DEV_PASSWORD, and every non-demo user just needs a
# NOT NULL value that no password can satisfy.
_DEMO_HASH = hash_password(DEV_PASSWORD)
_UNUSABLE_HASH = hash_password(secrets.token_urlsafe(32))

# Local dev: repo_root/seed/data. Container: /seed/data (compose bind mount).
_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "seed" / "data"


class SeedResult:
    def __init__(self, *, skipped: bool, counts: dict[str, int]) -> None:
        self.skipped = skipped
        self.counts = counts

    def __str__(self) -> str:
        if self.skipped:
            return "seed: seed_marker present -- nothing to do"
        c = self.counts
        return (
            "seed: loaded "
            f"{c['providers']} providers, {c['provider_staff']} staff, "
            f"{c['users']} users, {c['patients']} patients "
            f"({c['patients_unclaimed']} unclaimed)"
        )


def _data_dir() -> Path:
    return Path(os.environ.get("SEED_DATA_DIR", _DEFAULT_DATA_DIR))


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _dataset_checksum(identity_dir: Path) -> str:
    h = hashlib.sha256()
    for name in sorted(p.name for p in identity_dir.glob("*.csv")):
        h.update((identity_dir / name).read_bytes())
    return h.hexdigest()


async def _already_loaded(session: AsyncSession) -> bool:
    result = await session.execute(text("SELECT count(*) FROM seed_marker"))
    return bool(result.scalar_one())


def _build_objects(identity_dir: Path) -> tuple[list[object], dict[str, int]]:
    providers = [
        Provider(
            id=uuid.UUID(r["id"]),
            name=r["name"],
            kind=ProviderKind(r["kind"]),
            city=r["city"],
            state=r["state"],
        )
        for r in _rows(identity_dir / "providers.csv")
    ]

    users = []
    for r in _rows(identity_dir / "users.csv"):
        demo = r["demo_login"] == "1"
        users.append(
            User(
                id=uuid.UUID(r["id"]),
                email=r["email"],
                password_hash=_DEMO_HASH if demo else _UNUSABLE_HASH,
                role=Role(r["role"]),
                email_verified_at=VERIFIED_AT if demo else None,
            )
        )

    patients = []
    unclaimed = 0
    for r in _rows(identity_dir / "patients.csv"):
        uid = r["user_id"] or None
        if uid is None:
            unclaimed += 1
        patients.append(
            Patient(
                id=uuid.UUID(r["id"]),
                user_id=uuid.UUID(uid) if uid else None,
                full_name=r["full_name"],
                date_of_birth=date.fromisoformat(r["date_of_birth"])
                if r["date_of_birth"]
                else None,
                sex=Sex(r["sex"]) if r["sex"] else None,
                phone=r["phone"] or None,
                address_line=r["address_line"] or None,
                city=r["city"] or None,
                state=r["state"] or None,
                locale_preference=r["locale_preference"] or "en",
            )
        )

    staff = [
        ProviderStaff(
            id=uuid.UUID(r["id"]),
            user_id=uuid.UUID(r["user_id"]),
            provider_id=uuid.UUID(r["provider_id"]),
        )
        for r in _rows(identity_dir / "provider_staff.csv")
    ]

    counts = {
        "providers": len(providers),
        "provider_staff": len(staff),
        "users": len(users),
        "patients": len(patients),
        "patients_unclaimed": unclaimed,
    }
    # users + providers before patients + staff (FK order).
    return [*providers, *users, *patients, *staff], counts


async def run_seed() -> SeedResult:
    identity_dir = _data_dir() / "identity"
    if not (identity_dir / "patients.csv").is_file():
        raise FileNotFoundError(f"seed dataset not found under {identity_dir}")

    async with async_session() as session:
        if await _already_loaded(session):
            return SeedResult(skipped=True, counts={})

        objects, counts = _build_objects(identity_dir)
        session.add_all(objects)
        await session.flush()
        await session.execute(
            text(
                "INSERT INTO seed_marker (id, dataset_sha256) VALUES (1, :h)"
            ),
            {"h": _dataset_checksum(identity_dir)},
        )
        await session.commit()
        return SeedResult(skipped=False, counts=counts)


async def _main() -> None:
    result = await run_seed()
    print(result)


if __name__ == "__main__":
    asyncio.run(_main())
