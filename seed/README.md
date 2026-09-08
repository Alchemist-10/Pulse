# seed/

Synthea-generated clinical data with a deterministic Indian identity
overlay. Decision + reasoning: [ADR-0015](../docs/adr/0015-synthea-plus-indian-overlay-seed-data.md).
Operational spec and the two identity gaps: [`docs/seed-data.md`](../docs/seed-data.md).

**Pulse never holds real patient data.** Everything here is synthetic by
construction.

## What is committed vs generated

| Path | Committed? | Loaded in Phase 1? |
|---|---|---|
| `data/identity/*.csv` | yes | **yes** — first-boot loader |
| `data/clinical/*.csv` | yes (~15 MB) | **no** — staged for Phase 2 (no clinical tables yet) |
| `data/reference/pincodes.csv` | yes | as address source during regeneration only |
| `data/MANIFEST.json` | yes | no — provenance + row counts + csv hashes |
| `raw/` (Synthea output), the ~192 MiB jar | **no** — git-ignored | — |

Phase 1 has no `medical_entry` tables. `seed_loader.py` loads Provider,
ProviderStaff, User and Patient and nothing else; it never opens
`data/clinical/`.

## Layout

```
seed/
  requirements.txt          generation-time deps (Faker) — NOT a backend dep
  synthea/synthea.properties reference copy of the non-default Synthea flags
  providers/ml_in/          project-local ml_IN Faker person provider (Gap 1)
  scripts/
    common.py               every pin: Synthea version, seeds, population, paths
    run_synthea.py           verify jar checksum -> run jar -> seed/raw/
    build.py                 overlay + duplicate planting + write seed/data/
  data/                      the committed dataset (see table above)
  tests/test_loader.py       loader vs a fresh migrated Postgres (testcontainers)
```

## First boot (no regeneration needed)

`docker compose up` on a fresh clone:

1. `backend/entrypoint.sh` runs `alembic upgrade head`.
2. Then `python -m app.db.seed_loader`. It checks the `seed_marker` row
   (migration `0003`); absent -> load `data/identity/`, then write the
   marker. Present -> no-op. So a second `docker compose up` changes
   nothing.
3. `compose.yaml` bind-mounts `./seed/data` to `/seed/data:ro`; the loader
   resolves that path automatically (`SEED_DATA_DIR` overrides it).

## Demo credentials

Seeded, public, dev-only. Two Patients have a known password and a stamped
`email_verified_at` so the Phase 1 demo journey (sign in → view profile →
switch to Hindi) works against real rows:

| email | password | role | locale |
|---|---|---|---|
| `demo.patient.en@pulse.test` | `Pulse@demo1` | PATIENT | en |
| `demo.patient.hi@pulse.test` | `Pulse@demo1` | PATIENT | hi |
| `staff000@pulse.test` | `Pulse@demo1` | PROVIDER_STAFF | — |
| `clinician0@pulse.test` | `Pulse@demo1` | CLINICIAN | — |

Every other seeded User gets a random unusable hash. The dataset itself
carries **no** password hashes — argon2 output is non-deterministic and
would break the regenerate contract; the loader hashes `Pulse@demo1` at
load time for the rows flagged `demo_login=1` in `users.csv`.

## Planted pairs (`data/identity/planted_pairs.csv`)

For duplicate-detection work in a later phase. Each planted twin is a
fresh **Unclaimed** Patient (a provider filed it):

| kind | technique | shares |
|---|---|---|
| duplicate | `token_order_swap` | given/surname order flipped, same DOB + phone |
| duplicate | `dob_typo` | DOB off by a day or two, same name + phone |
| duplicate | `initials_vs_expanded` | "Aishani Toor" vs "A. Toor", same DOB + phone |
| near_miss | `sibling_same_surname_adjacent_dob` (×2) | surname + sentinel prefix only; different given name, DOB ±1–2 y, different phone |

The near-misses are the point: with only true pairs planted, precision
can be demonstrated but not measured (ADR-0015).

## Regenerating (needs Java)

Regeneration is off the critical path — only needed when the schema or the
overlay changes. Verified toolchain:

- **JDK: Eclipse Temurin 21.0.5+11** (`OpenJDK21U-jre_x64_linux_hotspot_21.0.5_11`).
  Any Java 21 JRE works. No system install needed — a portable tarball is
  fine; the backend images never get a JDK.
- **Synthea `v4.0.0`** — `synthea-with-dependencies.jar`, sha256
  `ed43c20ad40ba5c3bc724503a5af032715fe3c491620b766148e7c2361e6ecc1`
  (201 164 144 B). `run_synthea.py` refuses to run a jar whose size or
  hash does not match the pin.

```bash
# 1. deps
python3.13 -m venv .venv && .venv/bin/pip install -r seed/requirements.txt

# 2. the pinned jar (git-ignored)
curl -L -o synthea-with-dependencies.jar \
  https://github.com/synthetichealth/synthea/releases/download/v4.0.0/synthea-with-dependencies.jar

# 3. generate -> seed/raw/   (~30 s for 120 patients)
SYNTHEA_JAR=synthea-with-dependencies.jar JAVA_BIN=/path/to/java \
  .venv/bin/python -m seed.scripts.run_synthea

# 4. overlay + plant + write seed/data/
PYTHONPATH=. .venv/bin/python -m seed.scripts.build

# 5. the contract: nothing changed
git diff --stat seed/data
```

Step 5 must be empty. If it is not, a pin moved — reconcile
`seed/scripts/common.py` and `docs/tech-stack.md` before committing.

## Tests

```bash
uv run --project backend pytest seed/tests/       # needs Docker
```

Spins its own `postgres:18.6`, runs `alembic upgrade head`, then asserts:
deterministic row counts, ≥1 Unclaimed Patient, a second run is a no-op,
and both a planted duplicate pair and a near-miss pair are present and
identifiable.

## CI

- **Seed loader test** — the pytest above, on the Docker-capable runner
  (same one Phase 1 integration tests need).
- **Determinism guard** *(optional, needs a JRE on the runner)* — run
  `seed.scripts.build` against a committed `seed/raw/` fixture, or the
  full `run_synthea` + `build`, then `git diff --exit-code seed/data`.
- No JDK anywhere in the runtime images or their CI build — asserted by
  the Dockerfile.
