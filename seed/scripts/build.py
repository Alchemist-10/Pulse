"""Transform ``seed/raw/`` (Synthea) into the committed ``seed/data/`` set.

Pipeline (all deterministic, single fixed ``OVERLAY_SEED``):

    raw Synthea csv
      -> Indian identity overlay      (names / phone / address)
      -> duplicate + near-miss planting
      -> seed/data/identity/*.csv     (loaded on first boot, Phase 1)
      -> seed/data/clinical/*.csv     (committed, NOT loaded in Phase 1)
      -> seed/data/MANIFEST.json

Run after ``run_synthea``::

    python -m seed.scripts.build

Re-running with the same pins must produce a byte-identical ``seed/data``
(``git diff`` empty) -- that is the ADR-0015 contract and the loader test
asserts the row-count half of it.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import random
from dataclasses import asdict, dataclass, field

from faker import Faker
from seed.providers.ml_in import Provider as MlInPerson
from seed.scripts import common

# --- overlay row shapes -------------------------------------------------


@dataclass
class PatientRow:
    id: str
    user_id: str  # "" == Unclaimed Patient (user_id IS NULL)
    full_name: str
    date_of_birth: str
    sex: str
    phone: str
    address_line: str
    city: str
    state: str
    locale_preference: str


@dataclass
class UserRow:
    id: str
    email: str
    role: str
    demo_login: str  # "1" -> loader hashes DEV_PASSWORD + verifies


@dataclass
class ProviderRow:
    id: str
    name: str
    kind: str
    city: str
    state: str


@dataclass
class StaffRow:
    id: str
    user_id: str
    provider_id: str


@dataclass
class Bundle:
    patients: list[PatientRow] = field(default_factory=list)
    users: list[UserRow] = field(default_factory=list)
    providers: list[ProviderRow] = field(default_factory=list)
    staff: list[StaffRow] = field(default_factory=list)
    planted: list[dict[str, str]] = field(default_factory=list)


# --- fixed provider roster (deterministic, hand-set) -----------------

_PROVIDERS = [
    ("Aster Medcity", "HOSPITAL", "Kochi", "Kerala"),
    ("Apollo Hospitals", "HOSPITAL", "Chennai", "Tamil Nadu"),
    ("Sir Ganga Ram Hospital", "HOSPITAL", "New Delhi", "Delhi"),
    ("Ruby Hall Clinic", "CLINIC", "Pune", "Maharashtra"),
    ("SRL Diagnostics", "LAB", "Ahmedabad", "Gujarat"),
    ("Thyrocare Technologies", "LAB", "Bhubaneswar", "Odisha"),
]


def _faker_pool() -> dict[str, Faker]:
    pool: dict[str, Faker] = {}
    for loc in set(common.OVERLAY_LOCALES):
        if loc == "ml":
            f = Faker("en_IN")
            f.add_provider(MlInPerson)
        else:
            f = Faker(loc)
        Faker.seed(common.OVERLAY_SEED)
        f.seed_instance(common.OVERLAY_SEED)
        pool[loc] = f
    return pool


def _load_pincodes() -> list[dict[str, str]]:
    with common.PINCODES_CSV.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _read_synthea(name: str) -> list[dict[str, str]]:
    path = common.RAW_DIR / "csv" / name
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _name_for(fake: Faker, sex: str) -> str:
    return fake.name_male() if sex == "MALE" else fake.name_female()


def _tokens_swapped(name: str) -> str:
    parts = name.split()
    if len(parts) < 2:
        return name
    return " ".join([parts[-1], *parts[:-1]])


def _initials_form(name: str) -> str:
    parts = name.split()
    if len(parts) < 2:
        return name
    return f"{parts[0][0]}. {parts[-1]}"


def _dob_typo(iso: str, rng: random.Random) -> str:
    d = dt.date.fromisoformat(iso)
    # nudge the day by a small amount -> a plausible transcription slip
    delta = rng.choice([-2, -1, 1, 2])
    try:
        return (d + dt.timedelta(days=delta)).isoformat()
    except OverflowError:  # pragma: no cover
        return iso


def _adjacent_dob(iso: str, rng: random.Random) -> str:
    d = dt.date.fromisoformat(iso)
    years = rng.choice([-2, -1, 1, 2])
    try:
        return d.replace(year=d.year + years).isoformat()
    except ValueError:  # 29 Feb
        return d.replace(year=d.year + years, day=28).isoformat()


# --- overlay ---------------------------------------------------------


def overlay(bundle: Bundle) -> None:
    rng = random.Random(common.OVERLAY_SEED)
    fakers = _faker_pool()
    addr_faker = Faker("en_IN")
    addr_faker.seed_instance(common.OVERLAY_SEED)
    pincodes = _load_pincodes()

    src = sorted(_read_synthea("patients.csv"), key=lambda r: r["Id"])
    claimed_flags = [rng.random() < 0.7 for _ in src]
    # guarantee at least one of each
    claimed_flags[0] = True
    claimed_flags[1] = False

    user_ct = 0
    for sid_row, claimed in zip(src, claimed_flags, strict=True):
        sid = sid_row["Id"]
        sex = "MALE" if sid_row["GENDER"] == "M" else "FEMALE"
        loc = rng.choice(common.OVERLAY_LOCALES)
        name = _name_for(fakers[loc], sex)
        phone = common.PHONE_SENTINEL_PREFIX + f"{rng.randint(0, 99999):05d}"
        pin = rng.choice(pincodes)
        address_line = f"{rng.randint(1, 240)}, {pin['locality']}"

        pid = str(common.det_uuid("patient", sid))
        uid = ""
        if claimed:
            uid = str(common.det_uuid("user", sid))
            bundle.users.append(
                UserRow(
                    id=uid,
                    email=f"patient{user_ct:03d}@example.com",
                    role="PATIENT",
                    demo_login="",
                )
            )
            user_ct += 1

        bundle.patients.append(
            PatientRow(
                id=pid,
                user_id=uid,
                full_name=name,
                date_of_birth=sid_row["BIRTHDATE"],
                sex=sex,
                phone=phone,
                address_line=address_line,
                city=pin["city"],
                state=pin["state"],
                locale_preference=common.LOCALE_PREF[loc],
            )
        )

    _mark_demo_logins(bundle)


def _mark_demo_logins(bundle: Bundle) -> None:
    """Promote one EN and one HI claimed Patient to a known dev login, so the
    Phase 1 demo journey (sign in, switch to Hindi) works against real rows."""
    by_id = {p.id: p for p in bundle.patients}
    users_by_id = {u.id: u for u in bundle.users}
    want = {"en": "demo.patient.en@example.com", "hi": "demo.patient.hi@example.com"}
    for pref, email in want.items():
        for p in bundle.patients:
            if p.user_id and p.locale_preference == pref and p.id in by_id:
                u = users_by_id[p.user_id]
                u.email = email
                u.demo_login = "1"
                break
        else:  # pragma: no cover - population always covers en/hi
            raise RuntimeError(f"no claimed Patient with locale_preference={pref!r}")


# --- providers + staff --------------------------------------------


def build_providers(bundle: Bundle) -> None:
    for i, (nm, kind, city, state) in enumerate(_PROVIDERS):
        pv_id = str(common.det_uuid("provider", nm))
        bundle.providers.append(ProviderRow(pv_id, nm, kind, city, state))
        for s in range(2):
            u_id = str(common.det_uuid("staff-user", nm, str(s)))
            bundle.users.append(
                UserRow(
                    id=u_id,
                    email=f"staff{i:02d}{s}@example.com",
                    role="PROVIDER_STAFF",
                    demo_login="1" if (i, s) == (0, 0) else "",
                )
            )
            bundle.staff.append(
                StaffRow(
                    id=str(common.det_uuid("staff", nm, str(s))),
                    user_id=u_id,
                    provider_id=pv_id,
                )
            )
    for c in range(2):
        bundle.users.append(
            UserRow(
                id=str(common.det_uuid("clinician", str(c))),
                email=f"clinician{c}@example.com",
                role="CLINICIAN",
                demo_login="1" if c == 0 else "",
            )
        )


# --- planting ---------------------------------------------------------


_PREF_TO_LOCALE = {v: k for k, v in common.LOCALE_PREF.items()}


def _sibling_given_name(pref: str, sex: str, rng: random.Random) -> str:
    """A given name in the *same script* as the source Patient, for a
    plausible sibling. Fresh Faker so the overlay's stream is untouched."""
    loc = _PREF_TO_LOCALE[pref]
    if loc == "ml":
        f = Faker("en_IN")
        f.add_provider(MlInPerson)
    else:
        f = Faker(loc)
    f.seed_instance(rng.randint(0, 2**31))
    full = f.name_male() if sex == "MALE" else f.name_female()
    return full.split()[0].rstrip(".")


def plant(bundle: Bundle) -> None:
    rng = random.Random(common.OVERLAY_SEED ^ 0x5EED)
    pool = sorted(bundle.patients, key=lambda p: p.id)
    en_pool = [p for p in pool if p.locale_preference == "en"]

    def _clone(src: PatientRow, **over: str) -> PatientRow:
        base = asdict(src)
        base.update(over)
        # a planted twin is a fresh Unclaimed Patient (a provider filed it)
        base["id"] = str(common.det_uuid("planted", src.id, over.get("_tag", "x")))
        base.pop("_tag", None)
        base["user_id"] = ""
        return PatientRow(**base)

    # 1. token-order swap: "Ramesh Menon" vs "Menon Ramesh" (database.md:
    #    Indian naming order varies by region).
    a = pool[3]
    b = _clone(a, full_name=_tokens_swapped(a.full_name), _tag="swap")
    bundle.patients.append(b)
    bundle.planted.append(
        {"kind": "duplicate", "technique": "token_order_swap",
         "patient_id_a": a.id, "patient_id_b": b.id}
    )

    # 2. typo'd date of birth, name and phone identical.
    a = pool[7]
    b = _clone(a, date_of_birth=_dob_typo(a.date_of_birth, rng), _tag="dobtypo")
    bundle.patients.append(b)
    bundle.planted.append(
        {"kind": "duplicate", "technique": "dob_typo",
         "patient_id_a": a.id, "patient_id_b": b.id}
    )

    # 3. initials vs expanded: "Ramesh Menon" vs "R. Menon" (needs Latin script).
    a = en_pool[0] if en_pool else pool[11]
    b = _clone(a, full_name=_initials_form(a.full_name), _tag="initials")
    bundle.patients.append(b)
    bundle.planted.append(
        {"kind": "duplicate", "technique": "initials_vs_expanded",
         "patient_id_a": a.id, "patient_id_b": b.id}
    )

    # 4 + 5. near-miss non-duplicates: siblings -- same surname, adjacent DOB,
    #    different given name and phone. Genuinely different people.
    for idx, tag in ((17, "sib1"), (23, "sib2")):
        a = pool[idx]
        surname = a.full_name.split()[-1]
        given = _sibling_given_name(a.locale_preference, a.sex, rng)
        sib_phone = common.PHONE_SENTINEL_PREFIX + f"{rng.randint(0, 99999):05d}"
        b = _clone(
            a,
            full_name=f"{given} {surname}",
            date_of_birth=_adjacent_dob(a.date_of_birth, rng),
            phone=sib_phone,
            _tag=tag,
        )
        bundle.patients.append(b)
        bundle.planted.append(
            {"kind": "near_miss",
             "technique": "sibling_same_surname_adjacent_dob",
             "patient_id_a": a.id, "patient_id_b": b.id}
        )


# --- clinical transform (committed, NOT loaded in Phase 1) -----------

_CLINICAL_FILES = {
    "conditions.csv": ("START", "STOP", "PATIENT", "SYSTEM", "CODE", "DESCRIPTION"),
    "medications.csv": ("START", "STOP", "PATIENT", "CODE", "DESCRIPTION",
                        "REASONCODE", "REASONDESCRIPTION"),
    "observations.csv": ("DATE", "PATIENT", "CATEGORY", "CODE", "DESCRIPTION",
                         "VALUE", "UNITS", "TYPE"),
    "procedures.csv": ("START", "STOP", "PATIENT", "SYSTEM", "CODE",
                       "DESCRIPTION", "REASONCODE", "REASONDESCRIPTION"),
    "encounters.csv": ("Id", "START", "STOP", "PATIENT", "ENCOUNTERCLASS",
                       "CODE", "DESCRIPTION", "REASONCODE", "REASONDESCRIPTION"),
}


def transform_clinical() -> dict[str, int]:
    src_patients = {r["Id"] for r in _read_synthea("patients.csv")}
    id_map = {sid: str(common.det_uuid("patient", sid)) for sid in src_patients}
    counts: dict[str, int] = {}
    common.CLINICAL_DIR.mkdir(parents=True, exist_ok=True)
    for fname, cols in _CLINICAL_FILES.items():
        rows = _read_synthea(fname)
        out = common.CLINICAL_DIR / fname
        with out.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow([c.lower() for c in cols])
            n = 0
            for r in sorted(rows, key=lambda r: (r["PATIENT"], r.get("Id", ""),
                                                 next(iter(r.values())))):
                if r["PATIENT"] not in id_map:
                    continue
                r["PATIENT"] = id_map[r["PATIENT"]]
                w.writerow([r.get(c, "") for c in cols])
                n += 1
        counts[fname] = n
    return counts


# --- writers -------------------------------------------------------


def _write_csv(path: str, rows: list, header: list[str]) -> str:
    full = common.IDENTITY_DIR / path
    full.parent.mkdir(parents=True, exist_ok=True)
    with full.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            d = asdict(r) if hasattr(r, "__dataclass_fields__") else r
            w.writerow([d[h] for h in header])
    return hashlib.sha256(full.read_bytes()).hexdigest()


def write_dataset(bundle: Bundle) -> dict:
    bundle.patients.sort(key=lambda p: p.id)
    bundle.users.sort(key=lambda u: u.id)
    bundle.providers.sort(key=lambda p: p.id)
    bundle.staff.sort(key=lambda s: s.id)
    bundle.planted.sort(key=lambda p: (p["kind"], p["patient_id_a"]))

    hashes = {
        "patients.csv": _write_csv(
            "patients.csv", bundle.patients,
            ["id", "user_id", "full_name", "date_of_birth", "sex", "phone",
             "address_line", "city", "state", "locale_preference"],
        ),
        "users.csv": _write_csv(
            "users.csv", bundle.users, ["id", "email", "role", "demo_login"]
        ),
        "providers.csv": _write_csv(
            "providers.csv", bundle.providers,
            ["id", "name", "kind", "city", "state"],
        ),
        "provider_staff.csv": _write_csv(
            "provider_staff.csv", bundle.staff, ["id", "user_id", "provider_id"]
        ),
        "planted_pairs.csv": _write_csv(
            "planted_pairs.csv", bundle.planted,
            ["kind", "technique", "patient_id_a", "patient_id_b"],
        ),
    }
    return hashes


def write_manifest(bundle: Bundle, hashes: dict, clinical_counts: dict) -> None:
    unclaimed = sum(1 for p in bundle.patients if not p.user_id)
    manifest = {
        "generator": "synthea",
        "synthea_version": common.SYNTHEA_VERSION,
        "synthea_jar_sha256": common.SYNTHEA_JAR_SHA256,
        "synthea_patient_seed": common.SYNTHEA_PATIENT_SEED,
        "synthea_clinician_seed": common.SYNTHEA_CLINICIAN_SEED,
        "synthea_population": common.SYNTHEA_POPULATION,
        "overlay_seed": common.OVERLAY_SEED,
        "phone_sentinel_prefix": common.PHONE_SENTINEL_PREFIX.strip(),
        "counts": {
            "patients": len(bundle.patients),
            "patients_unclaimed": unclaimed,
            "users": len(bundle.users),
            "providers": len(bundle.providers),
            "provider_staff": len(bundle.staff),
            "planted_duplicate_pairs":
                sum(1 for p in bundle.planted if p["kind"] == "duplicate"),
            "planted_near_miss_pairs":
                sum(1 for p in bundle.planted if p["kind"] == "near_miss"),
        },
        "clinical_rows_committed_not_loaded": clinical_counts,
        "identity_csv_sha256": hashes,
        "note": (
            "Phase 1 loads identity only. clinical/ is committed for Phase 2 "
            "and is not read by the first-boot loader."
        ),
    }
    (common.DATA_DIR / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _write_clinical_readme(counts: dict[str, int]) -> None:
    lines = [
        "# seed/data/clinical",
        "",
        "Synthea clinical output, patient-id-remapped onto the overlaid Pulse",
        "Patient UUIDs. Coded vocabularies are preserved verbatim: SNOMED-CT",
        "(`conditions`, `procedures`), LOINC (`observations`), RxNorm",
        "(`medications`).",
        "",
        "**Not loaded in Phase 1.** Phase 1 has no clinical tables (`medical_entry`",
        "et al. are Phase 2). These files are committed now so the Phase 2 loader",
        "has a fixed, reviewed dataset to build against. `seed_loader.py` never",
        "reads this directory.",
        "",
        "US cost / payer / provider-identity columns are dropped in transform.",
        "Planted duplicate and near-miss Patients carry no clinical rows.",
        "",
        "| file | rows |",
        "|---|---|",
    ]
    for k, v in counts.items():
        lines.append(f"| `{k}` | {v} |")
    (common.CLINICAL_DIR / "README.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    bundle = Bundle()
    overlay(bundle)
    build_providers(bundle)
    plant(bundle)
    clinical_counts = transform_clinical()
    hashes = write_dataset(bundle)
    write_manifest(bundle, hashes, clinical_counts)
    _write_clinical_readme(clinical_counts)

    c = json.loads((common.DATA_DIR / "MANIFEST.json").read_text())["counts"]
    print("seed/data written:")
    for k, v in c.items():
        print(f"  {k:26} {v}")


if __name__ == "__main__":
    main()
