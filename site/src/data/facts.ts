// Every number and claim on the site comes from here, and every entry here
// cites the code it was checked against (2026-10-14). If the code changes,
// fix this file; never hand-type a count into a section.

export const REPO = "https://github.com/moneytosms/Pulse";
export const blob = (p: string) => `${REPO}/blob/main/${p}`;
export const tree = (p: string) => `${REPO}/tree/main/${p}`;

export const stats = {
  endpoints: 43, // 41 decorators in backend/app/modules/*/routes.py + 2 in app/main.py
  modules: 10, // backend/app/modules/*
  roles: 4, // app/core/authz.py:11-15
  permissions: 16, // app/core/authz.py:18-63
  entryKinds: 5, // app/modules/records/models.py:30-35 (EntryType)
  errorCodes: 21, // app/core/errors.py:8-33
  auditActions: 18, // app/modules/audit/models.py:28-47
  migrations: 9, // app/db/migrations/versions/0001..0009
  adrs: 16, // docs/adr/0001..0016
  locales: 4, // frontend/src/i18n/routing.ts:5
  catalogKeys: 540, // leaf keys per locale, frontend/src/i18n/messages/{en,hi,ta,ml}/*.json
  catalogFiles: 14, // per locale
  pages: 20, // frontend/src/app/[locale]/**/page.tsx
  backendTests: 273, // `uv run pytest` after #69 (testcontainers Postgres + Redis)
  e2eSpecs: 13, // frontend/e2e/*.spec.ts (mocked API)
  e2eTests: 78, // `npx playwright test --list`
  liveSpecs: 1, // frontend/e2e-live/demo-spine.live.spec.ts, real stack, no mocks
  ciLints: 4, // backend/scripts/lint_{cross_module_imports,module_sql,entry_query,actor_first}.py
  composeServices: 6, // compose.yaml
} as const;

export const roles = [
  {
    id: "PATIENT",
    name: "Patient",
    owns: "Owns the record. Reads their own timeline, grants and revokes consent, sees every access in their audit log, reads analytics and notifications.",
    cannot: "Cannot file or edit clinical entries.",
    permissions: 12,
  },
  {
    id: "PROVIDER_STAFF",
    name: "Provider Staff",
    owns: "Files Medical Entries for any existing Patient, including Patients who have never registered, attaches documents and files corrections.",
    cannot: "Can list only entries their own provider authored.",
    permissions: 4,
  },
  {
    id: "CLINICIAN",
    name: "Clinician",
    owns: "Reads a Patient's record only inside an active consent, filtered to its entry types, date window and expiry. Can request 60-minute emergency access with a written reason.",
    cannot: "The role alone grants no clinical access at all.",
    permissions: 5,
  },
  {
    id: "ADMINISTRATOR",
    name: "Administrator",
    owns: "Reviews duplicate Patient candidates, merges them and reverses merges.",
    cannot: "Cannot read clinical data on any endpoint, ever (ADR-0007). Holds no RECORDS_READ.",
    permissions: 4,
  },
] as const; // app/core/authz.py:66-108

export const entryKinds = [
  { kind: "DIAGNOSIS", table: "diagnosis", columns: ["code_system", "code", "display_name"] },
  { kind: "PROCEDURE", table: "procedure", columns: ["code_system", "code", "display_name"] },
  { kind: "PRESCRIPTION", table: "prescription", columns: ["medication_name", "dosage", "frequency", "route"] },
  { kind: "LAB_REPORT", table: "lab_report", columns: ["value_numeric", "value_text", "unit", "reference_low", "reference_high"] },
  { kind: "CLINICAL_NOTE", table: "clinical_note", columns: ["text"] },
] as const; // app/modules/records/models.py:82-141

export const seed = {
  synthea: "v4.0.0", // seed/scripts/common.py:15
  patientSeed: 424242, // common.py:27
  population: 120, // common.py:29
  overlaySeed: 20260901, // common.py:33
  phonePrefix: "+91 90000", // common.py:46 (sentinel, not a real number range)
  patients: 125, // seed/data/MANIFEST.json:10 (120 Synthea + 5 planted)
  unclaimed: 37, // MANIFEST.json:11 (no user account: Provider files for them)
  users: 103, // MANIFEST.json:16
  providers: 6,
  staff: 12,
  rawRows: { conditions: 3908, encounters: 6290, medications: 5122, observations: 73845, procedures: 13226 },
  plantedDuplicates: 3, // token_order_swap, dob_typo, initials_vs_expanded (seed/scripts/build.py:308-370)
  plantedNearMisses: 2, // sibling_same_surname_adjacent_dob
  entryCapPerPatient: { diagnosis: 3, procedure: 2, prescription: 2, lab: 3 }, // backend/app/db/seed_loader.py:67-70
  overlayLocales: ["hi_IN", "ta_IN", "ml (project provider)", "en_IN", "gu_IN", "mr_IN", "or_IN"], // common.py:73
} as const;

export const dedup = {
  weights: { name: 0.5, dob: 0.3, phone: 0.2 }, // app/modules/users/service.py:248-252
  threshold: 0.5, // service.py:175
  blocking: ["trigram name match (pg_trgm, GIN index)", "same birth year", "same phone"], // users/repository.py:97-115
} as const;

export const consent = {
  minDays: 1,
  maxDays: 365, // app/modules/consent/service.py:67-68
  stepUpMinutes: 5, // app/core/sessions.py:24
  breakGlassMinutes: 60,
  breakGlassBannerHours: 72, // frontend/src/components/BreakGlassBanner.tsx
} as const;

export const sessions = { idleMinutes: 60, absoluteHours: 12 }; // app/core/sessions.py:22-23

export const stack = {
  backend: [
    { name: "Python", version: "3.13" },
    { name: "FastAPI", version: "0.141.1" },
    { name: "SQLAlchemy (async)", version: "2.0.52" },
    { name: "Pydantic", version: "2.13.4" },
    { name: "Alembic", version: "1.19.1" },
    { name: "pwdlib[argon2]", version: "0.3.1" },
    { name: "asyncpg", version: "0.31.0" },
  ], // backend/pyproject.toml
  frontend: [
    { name: "Next.js (App Router)", version: "16.3.2" },
    { name: "React", version: "19.2.8" },
    { name: "TypeScript", version: "6.0.3" },
    { name: "next-intl", version: "4.13.7" },
    { name: "Tailwind CSS", version: "4.3.3" },
    { name: "Radix UI / shadcn", version: "1.6.7" },
    { name: "Recharts", version: "3.8" },
  ], // frontend/package.json
  infra: [
    { name: "PostgreSQL", version: "18.6" },
    { name: "Redis", version: "8.8.2" },
    { name: "Caddy", version: "2.11.4" },
    { name: "Mailpit", version: "1.31.0" },
  ], // compose.yaml
  testing: [
    { name: "pytest + testcontainers", version: "9.1.1 / 4.15.0" },
    { name: "Playwright", version: "1.63.0" },
    { name: "ruff + mypy", version: "0.16.4 / 2.3.1" },
  ],
} as const;

export const demoLogins = [
  { role: "Patient (English)", email: "demo.patient.en@example.com" },
  { role: "Patient (Hindi)", email: "demo.patient.hi@example.com" },
  { role: "Provider Staff", email: "staff000@example.com" },
  { role: "Clinician", email: "clinician0@example.com" },
  { role: "Administrator", email: "admin0@example.com" },
] as const; // seed/data/identity/users.csv (synthetic), RUNNING.md

export const notImplemented = [
  "Administrator audit viewer",
  "User and role management",
  "Patient search (Patients are opened by exact ID)",
  "Provider-created Patient onboarding and account claim",
  "Password and email change",
  "Notifications for non-Patient roles (Clinicians are emailed)",
  "SMS delivery",
] as const; // docs/workflows/README.md, verified by audit 2026-10-14

/** Team credits. Placeholder until the team confirms names and slices. */
export const team = [
  { name: "Team member", slice: "Database", issue: 18 },
  { name: "Team member", slice: "Backend", issue: 19 },
  { name: "Team member", slice: "Frontend", issue: 20 },
  { name: "Team member", slice: "Platform", issue: 21 },
] as const;

export const course = { name: "Course name", institute: "Institute", guide: "Professor" } as const; // placeholder
