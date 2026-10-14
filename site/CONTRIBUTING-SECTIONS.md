# Section contract

The site tells the story of Pulse to a grader (a professor of software architecture, practices and patterns) in one long scroll, then hands off to the guide (`/guide/*`, which renders the repo's own docs). Every section follows this contract. The reference implementations are `src/sections/Hero.astro` and `src/sections/ConsentEngine.astro`: match their voice, density and craft.

## Truth
- Every claim must be true of the code on `main` today. Before writing a sentence about behaviour, open the code that implements it. Numbers come from `src/data/facts.ts`. If you need a fact that is not there, put it in `src/data/<your-batch>.ts` with a `// file:line` citation comment on every value. Never edit `facts.ts` (other agents are working in parallel).
- Ground truth for workflows: `docs/workflows/README.md` (audited against code on 2026-10-14). Architecture: `docs/architecture.md`, `docs/domain-model.md`, `docs/adr/*`. Seed: `docs/seed-data.md`, `seed/README.md`, `seed/data/MANIFEST.json`.
- Name gaps honestly. If something is not implemented (see `notImplemented` in facts.ts), do not imply it is. Learned rule: never state an unverified external fact. No health-statistics claims about India unless you cite a primary source you have actually read; prefer qualitative framing.
- Synthetic data only. Clinical content shown in examples is never translated.

## Voice
- Plain, specific, active. Write for a smart reader who has not seen the repo. Explain why, not just what.
- No em dashes. No marketing filler ("seamless", "robust", "cutting-edge", "revolutionary"). No exclamation marks.
- Architecture and pattern names appear where they genuinely apply and are explained in one clause, never as a list of buzzwords. Each pattern claim links to the code or ADR that proves it.
- Sentence case for headings. Chapter titles are claims, not labels ("Corrections never erase", not "Corrections").

## Design rules (from the frontend-design review)
- Colours: only the CSS variables in `src/styles/global.css`. No hex, no new colours. Domain state colours (`--critical`, `--consent-*`, `--audit-*`, `--break-glass`, `--superseded`) always come with a text label or icon: colour never carries meaning alone.
- Type: Noto Sans only, using the `--step-*` scale. `--font-mono` only for real code, identifiers, endpoints, SQL.
- Do NOT use: all-caps eyebrow labels, `A · B · C` middle-dot meta strings, `→` appended to links/buttons, emoji, identical card grids as the default layout, gradient washes as decoration, a big-number-with-small-label stat row. Numbered markers only for real sequences (steps of a workflow are a sequence).
- Vary layout between sections: sticky visual + scrolling steps, two-column text + diagram, full-width diagram, a table, an interactive. Two adjacent sections should not share a layout.
- Mobile first. Must work at 375px with no horizontal page scroll (wide tables/diagrams scroll inside their own container or reflow). Test at 375 and 1440.
- Dark and light both. Use `light-dark()`-backed variables only, so both themes work automatically.

## Structure
- One file per chapter in `src/sections/`, wrapping its content in `<Chapter id n title lede wide?>` (`src/components/Chapter.astro`). Use the chapter numbers you were assigned.
- Real code: `<CodeBlock code lang file lines>` with excerpts copied from the repo (trimmed, never rewritten; elided lines marked with `...`). Keep excerpts short (under ~30 lines).
- Screenshots: `<Screenshot name alt frame url>` (`src/components/Screenshot.astro`). Use only the names listed in "Screenshot names" below; missing images render a placeholder until the capture agent delivers them.
- Diagrams: inline SVG in the section, `viewBox`-based and responsive, strokes/fills from CSS variables via classes, text as real `<text>` with `font-family: inherit`, an accessible `<title>`/`aria-label` describing the mechanism. Draw the real mechanism (real table names, real function names, real arrows), not decorative boxes.
- Links into the guide: `${import.meta.env.BASE_URL.replace(/\/$/, "")}/guide/<slug>` where slug is the doc path without `docs/` and `.md` (e.g. `adr/0008-audit-log-is-append-only-by-grant`, `architecture`, `workflows`, `seed-data`, `seed`, `context`, `running`, `demo`). Code links: `blob("path")` from facts.ts.

## Motion (src/scripts/motion.ts)
- The hero owns the page's one orchestrated load moment. Elsewhere, motion answers scroll or a click and shows a mechanism (a packet moving through layers, a path drawing, a row being appended). No fade-up on every block.
- Available primitives, all reduced-motion safe and progressive (content is visible without JS):
  - `data-draw` on an SVG path/line (optional value = seconds) inside an element with `data-draw-root`: the stroke draws once when scrolled into view.
  - `data-stagger` on a container: its children enter once, staggered. Use sparingly (at most once per section).
  - `data-steps` on a container with `data-step` children: sets `data-active="<index>"` on the container and `data-current` on the step nearest mid-viewport. Pair with a `position: sticky` visual whose frames you show/hide with CSS on `[data-active="n"]`. This is the main workflow device.
  - `data-count="<n>"` on an element whose text is the final number: ticks up once.
  - For anything bespoke, write a component `<script>` importing `{ gsap, ScrollTrigger, reducedMotion }` from `../scripts/motion`, and do nothing when `reducedMotion()` is true. Keep JS small; prefer CSS.
- Accessibility: interactive controls are real `<button>`/`<input>` with labels, 44px targets, visible focus; `aria-live="polite"` on regions that change.

## Screenshot names (produced by the capture agent, PNG, synthetic seeded data)
Desktop is 1440x900 viewport, phone is 390x844.
- `home-desktop`, `home-desktop-dark`: `/en` landing
- `login-desktop`: `/en/login` with demo-account buttons
- `register-phone`, `verify-pending-phone`
- `timeline-phone`, `timeline-desktop`, `timeline-desktop-dark`: patient `/en/timeline`
- `timeline-filters-desktop`: timeline with a type filter applied (chips visible)
- `entry-detail-phone`: patient `/en/timeline/[entryId]` (lab report with reference range)
- `consent-list-phone`: `/en/consent`
- `consent-new-desktop`: `/en/consent/new` filled form; `consent-stepup-desktop`: review step with password prompt
- `audit-desktop`: patient `/en/audit` showing ENTRY_VIEWED / CONSENT_* rows
- `notifications-phone`: `/en/notifications`
- `analytics-desktop`: `/en/analytics` with lab trend chart
- `profile-phone`: `/en/profile` with Patient ID copy
- `clinician-home-desktop`: `/en/clinician` consented patients list
- `clinician-records-desktop`: `/en/patients/[id]/records` inside consent
- `clinician-denied-desktop`: same URL after revoke: not-found state with the emergency access form
- `breakglass-banner-phone`: patient timeline showing the break-glass banner
- `staff-new-entry-desktop`: `/en/timeline/new` filing a lab report
- `staff-entry-correction-desktop`: staff entry detail with the correction action
- `superseded-entry-phone`: patient entry showing corrected/superseded status
- `admin-desktop`: `/en/admin`; `admin-duplicates-desktop`: `/en/admin/duplicates` with planted candidates
- `timeline-hi-phone`, `timeline-ta-phone`, `timeline-ml-phone`: patient timeline in Hindi, Tamil, Malayalam

## Verify before you report
1. Preview your sections on a page at `src/pages/preview/<batch>.astro` (it imports `Base`, `Spine` and your sections inside `<div class="story" style="position:relative">`, plus the same `initReveals/initSteps/initCounts` script as `src/pages/index.astro`). Leave it in place; the orchestrator deletes previews.
2. `npm run build` and `npx astro check` pass with 0 errors and 0 warnings from your files.
3. Screenshot your preview at 375x812 and 1440x900, in light and dark, with Playwright (`node_modules/playwright`), scrolling through so scroll-triggered content is revealed. Look at the screenshots and fix what looks wrong: overflow, cramped spacing, low contrast, awkward wrapping, broken diagrams. Check `document.documentElement.scrollWidth` equals the viewport width.
4. Re-read every sentence against the code once more.
