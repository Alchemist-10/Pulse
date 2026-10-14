# Plan: landing-site
Date: 2026-10-14

## Goal
Build a scroll-driven story site plus guide for Pulse at `site/` (Astro + GSAP) and deploy it to GitHub Pages (`https://moneytosms.github.io/Pulse/`). It is written for the grader. It covers the problem, the promise, the actors, every workflow step by step, the architecture and the patterns we used (only where they apply), the data model, consent/audit internals, the seed-data pipeline, i18n, the tech stack and why we chose it, the ADRs, verification, what is novel, delivery and the team. A guide section renders the repo's own docs and ADRs, so every "why?" question is one click away and nothing is duplicated. In parallel, clean up the repo docs so the README, docs index, site and ADRs all link to each other and match the code.

## Constraints
- Single source of truth: every claim and number on the site comes from `site/src/data/facts.ts`, and every entry there was verified against the code (file:line recorded in a comment). No hand-typed counts in copy.
- Learned rule: no unverified external facts. No India health statistics unless we can cite a primary source; otherwise frame the problem qualitatively.
- Use the colour tokens from `frontend/src/app/globals.css` only (burgundy/porcelain oklch, light + dark). Use the Noto Sans families from `frontend/src/app/fonts.ts` via @fontsource. Nothing else on the palette.
- Motion: GSAP ScrollTrigger plus CSS. Everything degrades under `prefers-reduced-motion`. Pages work without JS. Mobile-first (375px), no horizontal scroll.
- Site copy is English only. One section shows the four locales using real screenshots. Clinical content is shown untranslated (rule).
- No real patient data. Screenshots use seeded synthetic identities only.
- Do not touch `backend/` or `frontend/` code. Doc edits fix drift, dead links or navigation only. The architecture is locked, so ADR substance is not rewritten.
- Check library APIs with `ctx7` before use (Astro, GSAP, @astrojs/mdx, Pages action). Pin exact versions.
- Copy style: no em dashes, concise.
- Branch `feat/landing-site`, conventional commits, PR to main.

## Story arc (sections, in scroll order)
1. Hero: "Your medical history, owned by you." An animated pulse line draws into a timeline.
2. Problem: fragmented, paper-bound, provider-owned records. Qualitative unless a source is verified.
3. Promise: the CLAUDE.md invariant, built up one clause at a time (own / contribute / consent / recorded).
4. Actors: Patient, Provider Staff, Clinician, Administrator, with role cards showing what each can and cannot do (admins can't read clinical data, ADR-0007).
5. Workflows (pinned, scrubbed by scroll, one per step, real screenshot + animated SVG overlay):
   register + email verify · provider files an entry for an unregistered patient (nullable user_id) · timeline + filters · grant consent with step-up · clinician reads · instant revoke (no step-up) · audit trail · correction via supersede · duplicate detection + human merge/unmerge · notifications · analytics · admin. The final list comes from `docs/workflows/` cross-checked against the code.
6. Architecture: animated diagram Caddy (same origin) → Next.js / FastAPI → Postgres / Redis (+ Mailpit). A click-through of the modular monolith layers routes → service → repository, and the adapters.
7. Data model: joined-table inheritance animation (trunk + subtype tables), supersede chain.
8. Consent engine: one query builder `accessible_entries`, 404 not 403 (an interactive toggle), no permission cache.
9. Audit: append-only by GRANT, one event per access, no clinical data in metadata.
10. Seed data: Synthea → Indian overlay → planted duplicates and near-misses → measurable precision.
11. i18n: live four-locale switcher over screenshots. Clinical text stays fixed.
12. Tech stack + why: each choice paired with the alternative rejected and the trap we pinned (TS 6, not 7, etc.).
13. Patterns, only where real: modular monolith, layered architecture, repository, ports & adapters, aggregate root, default-deny, append-only log, contract-first + stubs, compute-on-read. Each one links to code and its ADR.
14. ADR gallery: all 16 as "chose X over Y" cards linking to the guide.
15. Quality: CI, enforcement lints (route coverage, entry-query, cross-module imports), integration tests on real Postgres, Playwright live spine.
16. What's novel / different.
17. Delivery: phases 0 to 4.5 timeline, team credits (from git + #18 to #21).
18. FAQ: grader questions ("how was the dataset made", "why not JWT", "why monolith") linking into the guide.
19. Run it: `docker compose up --build -d --wait`.
Guide: `/guide/*` renders `docs/**/*.md`, `CONTEXT.md` and the ADRs through an Astro content loader, with a remark plugin that rewrites relative `.md` links to site routes. Sidebar + search (Pagefind).

## Tasks (owner · model · verification)
### P0 Facts (blocks everything)
- T0.1 Extract counts from code: endpoints/permissions, roles, entry kinds, error codes, ADRs, tests, locales, seed stats, CI jobs. **Haiku Explore x2 in parallel** (backend, frontend+seed). Output: a raw table with file:line.
- T0.2 Verify and write `site/src/data/facts.ts` + the workflow list. **Opus (me)**. Verify: spot-check each entry against the cited file:line.
### P1 Docs cleanup (parallel with P2)
- T1.1 Link check all markdown (lychee or a script). **Haiku**. Output: list of broken links (explicitly "none" if clean).
- T1.2 Find doc claims that drift from the code, per cluster (architecture+domain+api / delivery+demo+running / seed+tech-stack+learnings / workflows). **Sonnet x4 ReadOnly**. Output: claim, doc:line, code evidence, proposed fix. No edits.
- T1.3 Review drift findings, decide fixes. **Opus**.
- T1.4 Apply approved fixes + broken links, add site link to README + docs/README, add "Superseded" banner check on archive. **Sonnet DocWriter**. Verify: link check reruns clean.
### P2 Scaffold + design system (Opus, sets the quality bar)
- T2.1 `site/` Astro project, base `/Pulse`, tokens ported from globals.css, fonts, light/dark, layout, nav, section wrapper, motion primitives (reveal, pin-scrub, draw-path, counter), reduced-motion guard.
- T2.2 Two reference sections built fully by Opus: Hero + Consent engine. These set the copy voice and animation pattern that all others copy.
- T2.3 `.github/workflows/pages.yml` (build site, upload, deploy). Verify: `npm run build` + `astro check` clean.
### P3 Screenshots
- T3.1 `site/scripts/capture.ts` Playwright: compose up, log in as each seeded role (docs/demo.md, RUNNING.md), capture the key screens in light/dark at mobile + desktop, plus 4 locales on 2 screens. Compose down -v. **Sonnet**. Verify: images exist, Opus eyeballs them, no real data visible.
### P4 Sections (parallel after T2.2 + T0.2)
- T4.x Sections 2 to 19 and the guide loader, split into ~5 batches of related sections, each in its own files. **Sonnet x5**, given: facts.ts, the reference sections, the token file and the section contract. No new deps without asking.
- T4.y SVG diagrams (architecture, JTI, seed pipeline, consent flow). Part of the relevant Sonnet batch. Opus reviews accuracy against the code.
### P5 Polish + verify (Opus)
- T5.1 Full read-through for accuracy against facts.ts, a consistent voice, and transitions between sections.
- T5.2 Playwright smoke: every section renders, every internal link resolves (crawler), 375 + 1440 screenshots, reduced-motion pass.
- T5.3 Lighthouse (chrome-devtools MCP): perf/a11y/best-practices ≥ 90, contrast check in both themes.
- T5.4 Commit, PR, merge after review, enable Pages, confirm the live URL loads.

## Acceptance Criteria
- [ ] `cd site && npm run build` and `npx astro check` pass with no errors.
- [ ] Every number on the site traces to facts.ts, and every facts.ts entry cites code.
- [ ] Every workflow in docs/workflows that ships in code appears step by step. Backend-only gaps are labelled as such.
- [ ] The internal link crawler finds 0 broken links on the site; the markdown link check finds 0 in the repo.
- [ ] README → site → guide → ADR → code links all work both ways.
- [ ] Lighthouse ≥ 90 on all four categories (mobile). No horizontal scroll at 375px. Reduced-motion is fully usable.
- [ ] Light + dark both match the app palette.
- [ ] The Pages workflow deploys and the live URL serves the site.

## Unresolved Questions
Answered 2026-10-14: team + course credits = placeholders, filled at end. Pages via `gh api` OK. No video. Merge self after review.

- [ ] Team: git shows 3 people (Srimoneyshankar Ajith, Bharadwaj B Chand, Alchemist-10 / akshay.v.s24bcd15). Who is the 4th member, what are the full names, and who owned which slice (#18 db, #19 backend, #20 frontend, #21 platform)?
- [ ] Course name / institute / professor name for the hero or footer? (IIIT Kottayam is inferred from an email; not used unless confirmed.)
- [ ] Enable Pages: Settings → Pages → Source = "GitHub Actions". You do it, or I run `gh api` (a raw API call, which your rules discourage)?
- [ ] Existing video (`docs/video-script.md`): is there a recorded demo video to embed?
- [ ] OK to merge the PR myself after the review passes, or do you merge?

## Risks
- Context: this spans several windows. I `/checkpoint` after each phase. P0+P2 fit in one window. P4 is delegated so its output stays out of my context.
- Sonnet section quality drift: mitigated by the reference sections, a strict section contract and an Opus polish pass.

## Progress
<!-- appended per phase -->

### 2026-10-14 session 1
- P0 facts: done (site/src/data/facts.ts, cited). P1 docs: audit x5 + fixes committed 86a3f6c; linkcheck 0 broken (scratchpad/linkcheck.py).
- Found + fixed real bug: dedup never triggered; PR #69 merged (seed loader queues candidates; near-misses not queued).
- P2 scaffold committed 5d4c70a (Hero, ConsentEngine reference chapters, guide, Pagefind). Pages workflow 7a4bdd6; Pages enabled (build_type=workflow).
- P3 capture + P4 sections A-E delegated to Sonnet worktree agents (branches feat/site-screenshots, feat/site-sections-{a..e}); merge + Opus polish next.
- Build cmd: `cd site && npm run build && npx astro check`. Screenshot helper: scratchpad/shot.mjs.
- Batch A merged + fixed (a4770dc); chapters 1-3 wired into index.astro. Still running at usage cutoff: screenshots + sections B-E (worktrees under .claude/worktrees/agent-*, branches feat/site-screenshots, feat/site-sections-{b..e}).
- Next: merge each branch, wire chapters into index.astro in order (4 record-life, 5 sharing, 6 consent-engine, 7 audit, 8-11, 12-15, 16-21), delete src/pages/preview/*, grep dist for "Screenshot pending" and digit+word joins like "125patients" (Astro drops the space after an expression at line end), Opus read-through, Lighthouse, PR, merge, confirm Pages deploy. Team/course placeholders in facts.ts.

### 2026-10-15 continuation
- Recovered pushed `origin/feat/landing-site` at 67ac9f7. The missing B/C/D branches were not published; completed chapters 4, 5 and 7–15 with Luna subagents at high reasoning only, using the original section contract.
- Wired all 21 chapters and added a native chapter index. All 29 genuine synthetic app screenshots are referenced, with AVIF/WebP variants. Removed the preview-only route.
- Fixed the consent/proof selector collision, denied-audit projection wording, session/consent distinction, literal source excerpts, mobile guide navigation, no-JS role/locale visibility, and dark code-comment contrast.
- Added reproducible browser smoke and static link/asset checks to the Pages workflow; preview starts with an explicit background flag and readiness probe.
- Verified: Astro check 0 errors/warnings/hints; production build 40 pages and 39 searchable guide documents; crawler 2,577 local references, 317 anchors, 154 Markdown links, no failures; browser smoke 8 modes with 21 chapters, zero exceptions and no page overflow. Covers 375/768/1440 px light/dark, reduced motion and no JavaScript, plus the interactive mechanisms and guide search.
- Cross-checked the code facts, including 273 collected backend tests, 78 browser cases, role allocations, seed data and all locale catalogs. Team/course credits remain placeholders; no video exists.
- Fresh review identified the CI preview lifecycle and a desktop grid issue; both fixed and recaptured. Final scoped reviewer verdict: ship, no remaining findings. Final mobile Lighthouse: performance 94, accessibility 100, best practices 100, SEO 100. Native expandable source excerpts and deferred SVG setup reduce initial rendering work; the hero text remains visible at first paint.
- Publishing constraint: signed-in `bharadwaj-b-chand04` has read-only access to `moneytosms/Pulse`, but owns its fork. Prepare the PR from the fork after review; upstream merge/deploy requires write access. Existing Pages configuration is already workflow-based.
