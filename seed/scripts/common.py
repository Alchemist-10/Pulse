"""Shared constants, paths and deterministic helpers for the seed pipeline.

Every value that influences the committed dataset is pinned here. Change
one and the dataset changes -- so a change here must be followed by a
regenerate + commit (see ``seed/README.md``).
"""

from __future__ import annotations

import uuid
from pathlib import Path

# --- pinned inputs --------------------------------------------------------

SYNTHEA_VERSION = "v4.0.0"
SYNTHEA_JAR_URL = (
    "https://github.com/synthetichealth/synthea/releases/download/"
    "v4.0.0/synthea-with-dependencies.jar"
)
SYNTHEA_JAR_SHA256 = (
    "ed43c20ad40ba5c3bc724503a5af032715fe3c491620b766148e7c2361e6ecc1"
)
SYNTHEA_JAR_SIZE = 201_164_144

# Two independent Synthea seeds (ADR-0015: "patient-generating and
# clinician-generating are separate seeds").
SYNTHEA_PATIENT_SEED = 424242
SYNTHEA_CLINICIAN_SEED = 20260901
SYNTHEA_POPULATION = 120
SYNTHEA_LOCATION = "Massachusetts"  # overlaid away; only clinical rows survive

# Drives the Indian identity overlay (Python ``random`` + ``Faker.seed``).
OVERLAY_SEED = 20260901

# --- demo credentials ---------------------------------------------------

# This project never holds real patient data (clinical-safety.md). The dev
# password is intentionally public and lives only in seed data.
DEV_PASSWORD = "Pulse@demo1"  # documented public demo credential
# A fixed instant so ``email_verified_at`` is deterministic in the CSV-free
# path; the loader stamps it, the dataset never carries an argon2 hash.
VERIFIED_AT = "2026-01-01T00:00:00+00:00"

# --- Pulse sentinel phone block (seed-data.md Gap 2) -------------------

PHONE_SENTINEL_PREFIX = "+91 90000 "

# --- deterministic id namespace --------------------------------------

# uuid5 off this root -> the same logical row gets the same UUID on every
# machine and every regenerate, so patient<->user links are stable.
_NS = uuid.uuid5(uuid.NAMESPACE_DNS, "seed.pulse.local")


def det_uuid(*parts: str) -> uuid.UUID:
    """Deterministic UUID for a logical key, e.g. ``det_uuid("patient", sid)``."""
    return uuid.uuid5(_NS, ":".join(parts))


# --- paths -----------------------------------------------------------

SEED_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SEED_DIR.parent
RAW_DIR = SEED_DIR / "raw"  # git-ignored Synthea output cache
DATA_DIR = SEED_DIR / "data"
IDENTITY_DIR = DATA_DIR / "identity"
CLINICAL_DIR = DATA_DIR / "clinical"
REFERENCE_DIR = DATA_DIR / "reference"
PINCODES_CSV = REFERENCE_DIR / "pincodes.csv"

# Locale mix for the overlay. ``ml`` is the project-local provider; the
# rest are Faker's. Weighted roughly toward the four Pulse UI locales.
OVERLAY_LOCALES: tuple[str, ...] = (
    "hi_IN",
    "hi_IN",
    "ta_IN",
    "ta_IN",
    "ml",
    "ml",
    "en_IN",
    "en_IN",
    "gu_IN",
    "mr_IN",
    "or_IN",
)

# patient.locale_preference is a 2-letter code; map overlay locale -> it.
LOCALE_PREF = {
    "hi_IN": "hi",
    "ta_IN": "ta",
    "ml": "ml",
    "en_IN": "en",
    "gu_IN": "gu",
    "mr_IN": "mr",
    "or_IN": "or",
}
