# Plan: ask-your-record
Date: 2026-10-15

## Goal
Deterministic, rule-based "Ask your record" chat for patients. Free-text question maps to a fixed intent, runs a consent-filtered query, returns typed answer blocks rendered localised in the frontend. No LLM. WOW features: (1) "who looked at my records?" via audit log, (2) per-answer receipt showing entries used, consent filter and audit event, (3) inline answers: lab sparkline with reference range, "what changed since last visit" diff, (5) "what would a paramedic see?" emergency card preview.

## Constraints
- All clinical reads compose from `accessible_entries(actor, patient_id)`; actor required in every signature.
- New module `backend/app/modules/ask/` (routes/service/repository layering); calls records, audit, emergency card via service interfaces only, no cross-module tables.
- Chat history never persisted (would be a clinical copy outside consent).
- One audit event per question; metadata = intent name only, no clinical values, no entry names.
- Consent-denied / no data returns same "nothing found" shape, 404 semantics, never hints existence.
- Answers are template key + params; frontend renders from key. Clinical content (names, values) verbatim in every locale; only interface strings translated.
- Intent lexicons per locale (en, hi, ta, ml); hi/ta/ml marked unreviewed in `docs/locale-review.md`.
- Unmatched question: suggestion chips, no guessing.
- "Who accessed" answer: no clinical data; actor role + time + access type only. Respect existing audit-log visibility for patients.
- TS types generated from OpenAPI; new endpoint declares required permission; schemas inherit `PulseSchema`; coded error envelope.
- Write negative tests first.
- No new dependencies.

## Acceptance Criteria
- [ ] `POST /api/ask` (patient actor) returns `{intent, blocks[], receipt}`; route-coverage test passes.
- [ ] Intents: latest-lab, lab-trend, medications, allergies, conditions, what-changed, who-accessed, emergency-preview; unmatched returns suggestions.
- [ ] Negative test: patient A cannot get answers about patient B; revoked-consent clinician-owned data absent; response identical to "no data".
- [ ] Negative test: audit event for ask contains no entry names or values.
- [ ] Negative test: administrator actor gets no clinical blocks.
- [ ] Lab trend block includes points, reference range, out-of-range flags; frontend draws sparkline with icon/label, not colour alone.
- [ ] What-changed block lists entries added/superseded since last encounter date.
- [ ] Who-accessed block lists role/time/access type from audit log for chosen window; no clinical content.
- [ ] Receipt lists entry ids used, filter applied, audit event id; expandable in UI.
- [ ] Emergency-preview block matches `/emergency-card` output exactly.
- [ ] Questions in en/hi/ta/ml each resolve to correct intent (one test per locale per intent).
- [ ] Frontend chat panel on patient portal, mobile-first, suggestion chips, keyboard accessible; catalog files per locale; missing keys throw in dev/CI.
- [ ] No chat state in DB/Redis/localStorage.
- [ ] `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `npm run lint`, `npx tsc --noEmit`, `npm run test:e2e` green.
- [ ] ADR-0018 written (rule-based over LLM, no persistence); `docs/learnings.md` entry.

## Unresolved Questions (resolved, 2026-10-15)
- [x] who-accessed window: default 30d, allowed 7/30/90.
- [x] Reuse `audit.service.list_for_patient` + `AuditEventProjection`; no new audit read.
- [x] Fuzzy match: stdlib `difflib` (ponytail: swap to trigram util if lexicons grow).
- [x] Lexicons: self-written en/hi/ta/ml, flagged unreviewed in `docs/locale-review.md`.
- [x] Emergency preview: reuse `emergency.service.view_for_patient`; card not set up returns "nothing set up" message block.
- [x] Compose via `records.service` / `analytics.service` like analytics module; no new SQL.

## Tasks
<!-- Populated as work begins -->
1. Contracts: answer-block schemas, intent enum, service signatures (merge first).
2. Stub `/api/ask` with fixture blocks; frontend chat shell against stub.
3. Intent matcher + lexicons + negative tests.
4. Intent handlers via records/audit/emergency services.
5. Receipt + audit emission.
6. Frontend blocks: sparkline, diff, access list, card preview, receipt.
7. i18n catalogs, locale-review.md update, ADR-0018.

## Progress
<!-- DocWriter appends here at session end -->
