# Next steps

> **Archived 2026-10-14.** Point-in-time status from 2026-09-29; superseded by the closed issues and [`docs/verification-and-operations.md`](../verification-and-operations.md).

Status as of **2026-09-29**, after plans 004, 005 and 006 landed on `main`
(backend 229 tests, mocked Playwright 29/29, live spine 1/1 ×2, CI green on
all four jobs including the first real `e2e-live` run). Living tracker —
update it as items close. Detailed context: [`plans/README.md`](../../plans/README.md),
[#56](https://github.com/moneytosms/Pulse/issues/56), [`docs/delivery-plan.md`](../delivery-plan.md).

## 1. Remaining implementation plans (do these first)

| Order | Plan | Priority | Effort | Note |
|---|---|---|---|---|
| 1 | [`plans/002-gate-entry-form-to-provider-staff.md`](../../plans/002-gate-entry-form-to-provider-staff.md) — gate `/timeline/new` to Provider Staff with an up-front `/auth/me` gate | P2 | S | Backend already 403s; this is the UX gate. Written against 079e7df + the 2026-09-28 fix (now merged) — run its drift check against live files. |
| 2 | [`plans/003-copy-patient-id-button.md`](../../plans/003-copy-patient-id-button.md) — copy button for the Patient ID on the profile page | P3 | S | **Run after 002, sequentially** — both edit `frontend/e2e/demo-spine.spec.ts`. Still useful after 004: Provider Staff still need the id. |

## 2. #56 — P4.5 packaging (remaining acceptance criteria)

- [x] Playwright suite covers the full demo spine and is green in CI — *delivered by plan 006 (2026-09-29)*
- [ ] **Stub inventory empty** — `backend` CI job already runs `scripts/stub_inventory.py` and it reports 0; verify once more at packaging time and tick.
- [ ] **Locale review (hi / ta / ml)** — one native-speaker-equivalent checklist pass per language, or explicitly recorded as *unverified* per the "never state an unverified external fact" rule (see [`docs/locale-review.md`](../locale-review.md)). Tamil and Malayalam are machine-translated and unreviewed; Hindi likewise.
- [ ] **Demo rehearsal on a machine that is not the author's**, from a fresh `git clone`, following [`docs/demo.md`](../demo.md). One rehearsal happened pre-shadcn-rebuild (PR #59); nobody else has run it.
- [ ] **Docs consolidation pass** — `docs/learnings.md` and `.claude/decisions.md` current as of 2026-09-29; re-check at packaging.
- [ ] **Submission packaging** (deployment call already made: laptop Compose, 2026-09-23).

## 3. Known code gaps (small, deliberate — decide, don't drift)

- **`grantee_name` is never populated** in the consent wire schema (`backend/app/modules/consent/service.py` `_to_wire`), so the consent list titles rows with the grantee's **UUID** and the live spec matches on the id. Populate it via `users_service` and the UI reads better immediately.
- **No screen files a correction.** The backend supersedes entries correctly and entry detail shows "This entry corrects an earlier one.", but the demo can only *say* this (step 3 of `docs/demo.md`). Decide: build the flow or keep it out of scope and keep saying so.
- **No patient search** — every screen takes a pasted UUID, by design. The 2026-09-28 audit rejected "patient search for Provider Staff" and "patient-uploaded documents" as direction options, not defects; either needs a decision/ADR first (`plans/README.md` "Findings considered and rejected").
- **Registration no longer offers roles** (plan 005): new Clinicians / Provider Staff / Administrators must come from the seed or a future invite flow — if the team asks how to add one, that's `seed/` + a new plan.

## 4. CI / platform loose ends

- **`e2e-live` doesn't run on PRs yet** — a `pull_request` run was skipped as `action_required` (workflow-permission gate). Check Settings → Actions → Workflow permissions if PRs should run the full stack job.
- **`e2e-live` cost** — image build + dev compile costs minutes per run. Plan 006's maintenance note suggests gating it to `main` + PRs labelled `e2e` if CI time matters.
- **`ubuntu-latest` migrates to Ubuntu 26 beginning 2026-10-19** (GitHub runner-images #14748, surfaced as a CI annotation) — recheck the four jobs after the migration, especially the Compose/testcontainers ones.
- **`main` protection is described in `docs/delivery-plan.md` (CI green + one review) but direct pushes to `main` are happening.** Reconcile: either enable branch protection or amend the docs to match reality.

## 5. Housekeeping

- The stray `frontend/frontend/.next` build leftover (worth 231 phantom lint errors) was moved out of the repo on 2026-09-29 to `/tmp/pulse-stray-frontend-frontend`. If `npm run lint` suddenly reports 231 errors again, a nested `.next` reappeared — move it out, don't chase the errors.
- `frontend/next.config.ts` carries `allowedDevOrigins: ["*.trycloudflare.com"]` (committed 2026-09-29 as found in the working tree) — remove it if the Cloudflare tunnel dev preview isn't used.
- Verification stack commands for anything above: bring up with `docker compose up --build -d --wait` (always `--build`), live spec via `npm run test:e2e:live` from `frontend/`, teardown `docker compose down -v` for a clean reseed.
