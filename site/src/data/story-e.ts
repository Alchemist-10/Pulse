// Batch E facts (chapters 17 to 21). Every value cites the file it was
// checked against on 2026-10-14. Counts live in facts.ts, not here.

/** CI jobs, in file order. .github/workflows/ci.yml */
export const ciJobs = [
  {
    id: "backend",
    name: "backend",
    note: "Real PostgreSQL and Redis, started by testcontainers",
    steps: [
      { cmd: "uv sync --frozen --group dev", what: "Install pinned dependencies", kind: "setup" },
      { cmd: "generate_api.py --check", what: "OpenAPI and generated TypeScript types agree", kind: "gate" }, // scripts/generate_api.py docstring
      { cmd: "ruff check .", what: "Lint", kind: "gate" },
      { cmd: "mypy .", what: "Types", kind: "gate" },
      { cmd: "lint_cross_module_imports.py", what: "No domain reaches into another's tables", kind: "lint" },
      { cmd: "lint_module_sql.py", what: "No raw SQL in domain modules", kind: "lint" },
      { cmd: "lint_entry_query.py", what: "No select(MedicalEntry) outside the query builder", kind: "lint" },
      { cmd: "lint_actor_first.py", what: "Readers of personal data take an actor", kind: "lint" },
      { cmd: "stub_inventory.py", what: "Print remaining stub endpoints", kind: "gate" },
      { cmd: "pytest", what: "Integration suite against real containers", kind: "test" },
    ],
  },
  {
    id: "frontend",
    name: "frontend",
    note: "No server needed",
    steps: [
      { cmd: "npm ci", what: "Install pinned dependencies", kind: "setup" },
      { cmd: "npm run check:locales", what: "Same keys and interpolations in all four locales", kind: "gate" }, // frontend/scripts/check-locales.mjs
      { cmd: "npm run lint", what: "ESLint", kind: "gate" },
      { cmd: "npx tsc --noEmit", what: "Types", kind: "gate" },
      { cmd: "npm run build", what: "Production build", kind: "gate" },
    ],
  },
  {
    id: "frontend-e2e",
    name: "frontend-e2e",
    note: "Playwright with the API mocked",
    steps: [
      { cmd: "npm ci", what: "Install", kind: "setup" },
      { cmd: "playwright install chromium", what: "Browser", kind: "setup" },
      { cmd: "playwright test", what: "Mocked browser suite", kind: "test" },
    ],
  },
  {
    id: "e2e-live",
    name: "e2e-live",
    note: "The whole stack, nothing mocked",
    steps: [
      { cmd: "docker compose up --build -d --wait", what: "Boot six services", kind: "setup" },
      { cmd: "npm ci and playwright install", what: "Install", kind: "setup" },
      { cmd: "npm run test:e2e:live", what: "Drive the real spine", kind: "test" },
      { cmd: "docker compose logs --tail 300", what: "Runs only on failure", kind: "setup" },
    ],
  },
] as const;

/** The live spine, in order. frontend/e2e-live/demo-spine.live.spec.ts:25 test title; docs/verification-and-operations.md "Reproduce the checks" */
export const liveSpine = [
  "Provider Staff files an entry",
  "Patient grants consent, with step-up",
  "Clinician reads the record",
  "Patient sees the access in the audit log",
  "Patient revokes",
  "Clinician is locked out",
] as const;

/** docs/delivery-plan.md, phase headings and status lines. */
export const phases = [
  {
    id: "p0",
    name: "Phase 0, bootstrap",
    landed: "The repo skeleton in one empty commit, Compose with six services, Caddy same-origin routing, CI green on an empty repo, the error envelope, the first migration with two database roles, the Next.js shell with the locale matcher excluding /api.", // delivery-plan "Phase 0"
    exit: "docker compose up starts six containers and CI is green.", // "Exit:"
    issue: null, // no closing issue named in the plan
  },
  {
    id: "p1",
    name: "Phase 1, skeleton",
    landed: "Register, verify by email, log in, see a seeded Patient, switch to Hindi. The route-coverage test, the entry-query lint and the cross-module import lint landed here, against three endpoints.", // "Phase 1"
    exit: "A fresh clone boots, seeded, and logs in. Met 2026-09-08.", // "Gate to Phase 2"
    issue: 23, // "Status: complete ... #23"
  },
  {
    id: "p2",
    name: "Phase 2, records spine",
    landed: "The medical_entry trunk and five subtype tables, provider upload with MIME sniffing, the patient timeline, corrections by supersession.", // "Phase 2"
    exit: "A Provider's upload appears on the Patient's timeline.", // "Gate to Phase 3"
    issue: 24,
  },
  {
    id: "p3",
    name: "Phase 3, consent, audit, notifications",
    landed: "accessible_entries, consent grant behind step-up and revoke without, break-glass, the append-only audit table, notifications, and the adversarial suite of negative tests.", // "Phase 3"
    exit: "The whole spine works and every negative test is green. Nothing from Phase 4 started before this.", // "Gate to Phase 4"
    issue: 47,
  },
  {
    id: "p4",
    name: "Phase 4, analytics, admin, duplicates, locales",
    landed: "Analytics computed on read, the administrator console with no clinical data, blocked-then-scored duplicate detection with reversible merges, Hindi, Tamil and Malayalam catalogs.", // "Phase 4"
    exit: "Catalogs delivered as recorded-unverified, not reviewed by a native speaker.", // Phase 4 Bharadwaj bullet, docs/locale-review.md
    issue: "52 to 55", // "issues #52–#55 closed"
    issues: [52, 53, 54, 55],
  },
  {
    id: "p45",
    name: "Phase 4.5, packaging",
    landed: "The live end-to-end spec and its CI job, a rehearsal on a fresh clone, documentation consolidated.", // learnings "mocked e2e suite" + demo.md "Rehearsed 2026-10-14" + Phase 4 "docs consolidation"
    exit: "Closed 2026-10-14.", // "Phase 4.5" status
    issue: 56,
  },
] as const;

/** CLAUDE.md "Learned rules" (verbatim claims), plus one from docs/learnings.md. */
export const learned = [
  {
    rule: "Contracts merge before implementations.",
    why: "Schemas and repository signatures first, stubs second, real code third. A person blocked waiting on someone else's implementation means a gate was skipped.", // CLAUDE.md
    link: "adr/0014-code-first-api-with-stub-endpoints",
  },
  {
    rule: "Enforcement tests are cheap early and unpayable late.",
    why: "The route-coverage test, the entry-query lint and the cross-module import lint landed against three endpoints, not sixty.", // CLAUDE.md
    link: "adr/0004-default-deny-route-authorization",
  },
  {
    rule: "Write the negative test first.",
    why: "A positive test passes just as happily when the access filter was never applied.", // CLAUDE.md
    link: "learnings",
  },
  {
    rule: "A green mocked suite is not an integration test.",
    why: "The backend required a password re-entry before granting consent, the form never sent one, every live grant failed, and CI stayed green because the mock accepted it. The live spec exists because of that.", // docs/learnings.md "The mocked e2e suite cannot see ..."
    link: "learnings",
  },
  {
    rule: "Never state an unverified external fact in project documentation.",
    why: "Two research passes hit blocked primary sources; both are recorded as unverified rather than smoothed over. This is why the locale review page says plainly that no native speaker has read the Hindi, Tamil or Malayalam.", // CLAUDE.md + docs/locale-review.md
    link: "locale-review",
  },
  {
    rule: "The interface is localised; clinical data is not.",
    why: "This one gets violated by accident, in the direction of helpfulness.", // CLAUDE.md
    link: "adr/0013-error-codes-not-messages",
  },
] as const;

/** RUNNING.md section 2, docs/verification-and-operations.md, frontend/package.json:15 */
export const runCommands = {
  clone: "git clone https://github.com/moneytosms/Pulse.git\ncd Pulse",
  up: "docker compose up --build -d --wait",
  live: "cd frontend\nnpm ci\nnpx playwright install --with-deps chromium\nnpm run test:e2e:live",
  down: "docker compose down -v",
} as const;
