# Pulse Design System v1.1 — archived

> This is a historical design proposal. The current burgundy material UI specification is [DESIGN.md](../../DESIGN.md), which supersedes the palette, surface, shadow, and glass restrictions below. Keep this file for decision history only.
**Companion to Pulse SRS v1.1 and Pulse UML Diagrams v1.0**
*Machine-readable reference, kept as decision history. The rules below were binding when written and are now superseded by DESIGN.md. The companion HTML preview was a rendering of these tokens, not a second source of truth.*

**Changelog from v1.0:** replaced the type system (Fraunces → Faustina, Public Sans → Elms Sans) with rationale in §2.0; fixed five implementation-drift bugs (thread node size, display type scale, primary-button hover shadow, consent icon, provenance icon); added five previously-missing components (§5.9–§5.13); added §11 research grounding.

---

## 0. What Pulse is (context an LLM needs before generating anything)

Pulse is a unified lifelong Electronic Health Record platform. Four user classes: **Patient** (owns the record, low-to-mixed technical literacy), **Clinician** (time-pressured, needs speed and critical info first), **Provider Staff** (uploads records from hospitals/labs), **Administrator** (compliance, audit, restricted medical-content visibility). The product's emotional job is to make a lifetime of fragmented, anxiety-adjacent medical paperwork feel **continuous, calm, and legible** — not clinical-cold, not consumer-cute.

Design direction in one sentence: **a warm paper chart that happens to be software** — Notion/Linear-grade structural discipline, a soft grain texture instead of sterile flat white, a muted clinical-blue chrome with a dusty-rose human accent used sparingly, and a serif used only where the product needs to sound like a person, not a system.

---

## 1. Color tokens (exact hex — do not approximate or reinvent)

### 1.1 Neutrals — "Paper & Ink" (the base of every screen)
| Token | Hex | Usage |
|---|---|---|
| `paper` | `#F6F4EF` | Page/app background. Always carries the grain texture (§7). Deliberately not `#FFFFFF` — a warm tint reads easier over long sessions than stark white (see §11). |
| `paper-raised` | `#FFFFFF` | Cards, modals, popovers — anything sitting "above" the page. |
| `paper-sunken` | `#EFEBE3` | Input fields, table row stripe, inset wells, code/mono blocks. |
| `ink-900` | `#211F1B` | Headings, primary text on paper-raised. |
| `ink-700` | `#4A453E` | Body text default. |
| `ink-500` | `#756F65` | Secondary/supporting text, captions, timestamps. |
| `ink-300` | `#A39C90` | Placeholder text, disabled labels. |
| `line` | `#E2DCD0` | Default border/divider. |
| `line-strong` | `#C9C1B2` | Table headers, emphasized dividers, input focus-adjacent borders. |

### 1.2 Primary — "Harbor" (clinical trust; the dominant chrome color)
| Token | Hex | Usage |
|---|---|---|
| `harbor-900` | `#1F4552` | Text-on-tint, high-emphasis headings when a blue heading is needed. |
| `harbor-700` | `#2F5D68` | Primary buttons, links, active nav, primary icon stroke. **This is "the" brand color.** |
| `harbor-500` | `#5B8998` | Secondary icons, chart lines, mid-emphasis UI, the Continuity Thread line. |
| `harbor-200` | `#C6DEE2` | Borders on tinted elements, focus rings. |
| `harbor-100` | `#E7F1F2` | Selected-state backgrounds, subtle info backgrounds. |

### 1.3 Secondary — "Bloom" (human warmth; accent only, never dominant)
| Token | Hex | Usage |
|---|---|---|
| `bloom-700` | `#A85468` | Hover/active state of secondary actions, emphasis text (rare). |
| `bloom-500` | `#C97B8B` | Secondary accent: illustration linework, empty-state graphics, patient-facing highlight. |
| `bloom-200` | `#F0D3D9` | Badge backgrounds (non-critical, e.g. "Patient" role chip). |
| `bloom-100` | `#FAECEE` | Subtle warm backgrounds (e.g. onboarding panels). |

**Hard cap: Bloom tones must never exceed ~10% of any single screen's colored surface area, and never appear as a primary button or as a status/semantic color.** It is seasoning, not the dish.

### 1.4 Semantic (status — always paired with an icon AND a text label, never color alone)
| State | Text | Fill/Icon | Background | Maps to (from UML) |
|---|---|---|---|---|
| Success / Allowed / Active | `sage-700` `#3F6E52` | `sage-500` `#5B8C6E` | `sage-100` `#E4EFE6` | `AuditLogEntry.outcome = ALLOWED`, `AccessPermission.status = ACTIVE`, `MedicalEntry` state `Active`/`Current` |
| Warning / Pending / Flagged | `ochre-700` `#8A5A17` | `ochre-500` `#C1873A` | `ochre-100` `#F5E8D3` | `DataQualityFlag`, `PendingReview`, `DuplicateReviewItem` state |
| Critical / Denied / Rejected | `brick-700` `#8C2E26` | `brick-500` `#C1443A` | `brick-100` `#F5DEDB` | `outcome = DENIED / FAILED_VALIDATION`, `Rejected` state, expired `ConsentRecord` |
| Neutral / Historical | `ink-500` `#756F65` | `ink-300` `#A39C90` | `paper-sunken` `#EFEBE3` | `Superseded`, `Merged`, `Hidden` states — deliberately *not* a semantic color, because these are not errors, they are normal lifecycle (§5.9) |

**Rule:** red-green color blindness affects ~8% of male users. Never let a semantic state be conveyed by hue alone — always pair with an icon shape (check / triangle / cross / clock) and a text label.

### 1.5 Absolute bans
- No gradients, anywhere, for any reason — not on buttons, heroes, backgrounds, or icons. Flat fills only.
- No pure black `#000000` and no pure white `#FFFFFF` used as a text/background *pair* (use `ink-900` on `paper-raised`, never `#000` on `#FFF`).
- No neon/saturated hues (no `#00C2FF`-style bright blue, no hot pink, no pure red `#FF0000`).
- No terracotta/burnt-orange/clay accent color (a well-known "AI-generated design" tell — avoid entirely).
- No glassmorphism, no background blur panels, no colored drop-shadows (e.g. a blue-tinted glow under a card). Shadows are always neutral, see §6.

---

## 2. Typography

### 2.0 Why these three fonts (decision record — do not silently swap fonts without updating this)

Three candidate fonts were evaluated against this brief (Elms Sans, Zen Kurenaido, Faustina) alongside the incumbent pair (Fraunces, Public Sans):

- **Zen Kurenaido — rejected.** Ships as a single weight (Regular only, no bold/medium/light), which makes it structurally unable to carry a type hierarchy on its own. It is also an explicitly handwritten/brush-derived Japanese-Latin design — expressive and informal, which undercuts the "trustworthy clinical record" register the product needs. Right font, wrong product.
- **Fraunces — retired.** Not wrong, but has become one of the most recognizable "AI-generated warm SaaS doc" serif defaults. Faustina delivers the same reassuring/editorial job with a lower-cliché footprint and a taller x-height (better small-size legibility).
- **Public Sans — retired.** A reasonable, purpose-built civic-service font, but Elms Sans is a better fit for this specific brief: a full 9-weight variable range (Thin–Black), an explicitly stated design goal of "quiet precision... subtle warmth in proportions" for design systems, and it is new enough (late-2025 release) to not yet read as a template default the way Inter/Public Sans increasingly do.
- **IBM Plex Mono — kept unchanged.** Still the correct purpose-built choice for machine-generated values; nothing in this review surfaced a reason to replace it.

**Result: Faustina (display) · Elms Sans (all UI) · IBM Plex Mono (data). Exactly three families — never substitute or add a fourth.**

### 2.1 Typeface roles
| Role | Family | Fallback stack | Where it's used |
|---|---|---|---|
| Display | **Faustina** (variable, weight axis 300–800) | `Faustina, Georgia, 'Iowan Old Style', serif` | Marketing headlines, section dividers, empty-state headlines, the wordmark. **Never body copy. Never buttons. Never table/data content.** |
| UI / Body | **Elms Sans** (variable, weight axis 100–900) | `'Elms Sans', -apple-system, 'Segoe UI', sans-serif` | Everything else: nav, buttons, form labels, body text, headings inside the product (H3 and smaller), captions. |
| Data / Mono | **IBM Plex Mono** | `'IBM Plex Mono', ui-monospace, monospace` | IDs (`recordId`, `userId`), timestamps, ABHA numbers, audit log rows, version numbers, code-like structured values. |

**Rule of thumb:** if a human wrote the sentence to be *read*, it's Elms Sans (or Faustina if it's a headline meant to feel human/reassuring). If a machine generated the value, it's IBM Plex Mono.

### 2.2 Type scale (rem, 16px root)
| Token | Size / Line-height | Weight / Family | Tracking |
|---|---|---|---|
| `display` | 3.5rem / 1.05 | Faustina 600 | -0.01em |
| `h1` | 2.5rem / 1.1 | Faustina 600 | -0.01em |
| `h2` | 1.75rem / 1.2 | Faustina 600 | normal |
| `h3` | 1.25rem / 1.3 | Elms Sans 600 | normal |
| `h4` | 1rem / 1.4 | Elms Sans 600 | normal |
| `body-lg` | 1.125rem / 1.6 | Elms Sans 400 | normal |
| `body` | 1rem / 1.6 | Elms Sans 400 | normal |
| `body-sm` | 0.875rem / 1.55 | Elms Sans 400 | normal |
| `eyebrow` | 0.75rem / 1.4 | Elms Sans 700, UPPERCASE | 0.08em |
| `data` | 0.8125rem / 1.5 | IBM Plex Mono 400 | normal |

**Rule:** never go smaller than `body-sm` (0.875rem) for anything a patient reads. Never set Faustina below 1.25rem (it loses its character and starts looking like a body-copy mistake).

### 2.3 Loading (reference implementation)
```html
<link href="https://fonts.googleapis.com/css2?family=Faustina:wght@300..800&family=Elms+Sans:wght@100..900&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
```
If Elms Sans is unavailable via Google Fonts in your build pipeline, self-host via `@fontsource-variable/elms-sans` (OFL-licensed, npm-distributed) rather than substituting a different sans — see §2.0 for why the substitution matters.

---

## 3. Spacing, grid, radius

### 3.1 Spacing scale (base unit 4px — all margins/padding/gaps must be a multiple of this)
`4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48 · 64 · 96` (px)

### 3.2 Radius scale (exactly three values — never an arbitrary radius)
| Token | Value | Usage |
|---|---|---|
| `radius-sm` | 8px | Inputs, small buttons, chips (non-pill) |
| `radius-md` | 12px | Cards, panels, modals |
| `radius-lg` | 20px | Hero panels, large illustration containers |
| `radius-pill` | 999px | Status badges, tab pills, avatar |

Never `0px` (too cold/broadsheet for this brief) and never above `20px` on rectangular containers (avoid bubbly/toy feeling).

---

## 4. Iconography

- **System:** Phosphor Icons, **Regular weight only**, rendered at 20px or 24px, stroke-equivalent ~1.5px, default color `ink-700`; `harbor-700` when active/selected; never filled/duotone/bold weight (mixing weights reads as inconsistent).
- **Custom marks required for four Pulse-specific concepts** (do not substitute a generic Phosphor icon for these):
  1. **Continuity** (the lifelong record itself) — a broken-then-rejoined line, echoing the "thread" motif.
  2. **Consent / Access grant** — an **open gate/latch**: two short horizontal bars with a gap between them (the "gate"), never a closed shackle-over-a-body shape. If your render looks like a padlock at any weight, it is wrong — redraw it. A padlock reads as "locked out"; Pulse is about the patient *granting* access, a different emotional register.
  3. **Provenance** (which provider a record came from) — a small circular **stamp/seal** mark (a ring with a short internal mark, like a wax-seal or postmark), never a teardrop/map-pin silhouette. If your render has a pointed bottom like a location pin, it is wrong — redraw it.
  4. **Non-clinical insight** (FR-6 summaries) — an outline chart mark with a small "i" or asterisk badge, never a stethoscope/heartbeat glyph (those imply diagnosis, which Pulse explicitly does not do — SRS §1).
- **Banned icon clichés:** red cross / plus-in-circle for anything except a literal "add" action, EKG heartbeat squiggle, generic stethoscope-in-circle as a catch-all "healthcare" icon, padlock for consent, map-pin for provenance, generic shield for "security" (use it only for the literal Administration/security-policy area, not sprinkled everywhere).

---

## 5. Components — spec summary

| Component | Rule |
|---|---|
| **Primary button** | `harbor-700` fill, `paper-raised` text, `radius-sm`, `body` weight 600, **`shadow-sm` on hover only** (resting state has no shadow). |
| **Secondary button** | `paper-raised` fill, 1px `line-strong` border, `ink-900` text. |
| **Destructive action** (e.g. revoke access) | Outline only by default (`brick-500` border + text on `paper-raised`), fills solid `brick-500` only on confirm step — never solid on first click, this is a healthcare app, no accidental one-click revocations. |
| **Status badge** | `radius-pill`, semantic bg + text pair from §1.4, always includes a small icon, 12px/`eyebrow`-style label. |
| **Card (record entry)** | `paper-raised`, `radius-md`, `shadow-sm`, 1px `line` border, provenance shown in `data` mono style bottom-right. |
| **Timeline / Continuity Thread** | See §5.8 for exact geometry. Never a solid flat rule — this is the signature element. |
| **Table (audit log, admin views)** | Header row `paper-sunken` bg + `line-strong` bottom border, `eyebrow` style header labels, body rows `data` mono for IDs/timestamps, `body-sm` for everything else, zebra striping optional at `paper-sunken` 50% only if row count > 8. |
| **Alert / inline banner** | Left 3px solid semantic-colored bar + semantic-100 background tint, never a full-bleed solid semantic color block (too alarming for a records app). |
| **Empty state** (§5.10) | Faustina `h2` headline, `bloom-500` line-art illustration, one primary action. |

### 5.8 The Continuity Thread — exact geometry (fixes v1.0 implementation drift)
The signature device: a hand-set dotted/dashed vertical line with small solid nodes at each event. Used anywhere chronology matters — patient timeline, audit log, access-history list, onboarding steps.
- **Line:** `harbor-500`, 1.5px dash width, 6px gap.
- **Node:** total rendered diameter **10px** = a 6px filled circle core (`harbor-700`, or the relevant semantic color for that node) + a 2px `paper-raised` ring around it for contrast against the paper background. (A bare 6px dot with no ring is nearly invisible on the warm paper tone — the ring is required, not decorative.)
- Do not reuse this motif decoratively outside chronological contexts; its meaning depends on scarcity.

### 5.9 Version / supersede history view (new — was missing in v1.0)
Directly implements the UML rule: *"Updates never overwrite. A correction creates a new version and links back to the entry it supersedes, preserving history."*
- Default view shows only the **current/active version** of each `MedicalEntry`, with a small `v{n}` mono tag and, if `version > 1`, a text link **"View earlier versions (n)"**.
- Expanding it reveals prior versions in `ink-500` (neutral, not semantic-colored — a superseded entry is not an error) each with its own timestamp, source, and a "superseded on {date}" caption.
- Superseded entries are visually **de-emphasized, never hidden or struck through** — strikethrough implies "wrong," but a superseded entry is historically accurate and legally must remain reconstructable (SRS §5.1, FR-2).

### 5.10 Duplicate review item (new — was missing in v1.0)
Implements `DuplicateReviewItem` from the UML (candidateA/candidateB/matchScore/state).
- Card shows the two candidate entries side by side (`paper-sunken` panels), the differing fields highlighted in `ochre-700`, and the `matchScore` as a plain-language label ("Likely duplicate" / "Possible duplicate") rather than a raw decimal — raw match-score decimals are an implementation detail, not something a provider or admin should have to interpret.
- Three actions, always in this order and never destructive-styled: **Merge** (secondary button), **Link as related, keep both** (secondary button), **Not a duplicate / Dismiss** (text button, no fill). None of these three is a `brick` destructive action — a wrong merge decision here is a data-integrity risk, not a delete, and should not visually imply irreversible danger.

### 5.11 Non-clinical insight labeling (new — was missing in v1.0; upgraded from a Do/Don't bullet to a hard component rule)
The UML stereotypes `SummaryInsight` as `«non clinical»`, and FR-6 requires the system to *"clearly label insights as informational and non-clinical."* This is a compliance requirement, not a style preference.
- Every chart, trend line, or summary card generated from `SummaryInsight` **must** carry a persistent, non-dismissible `eyebrow`-style tag reading **"Informational · Not a diagnosis"** in `ink-500` on `paper-sunken`, positioned at the top of the card, in the same visual position every time.
- This label is exempt from the "icon graveyard" concern — it is required even when it appears repetitive across a dashboard of multiple charts.

### 5.12 ABHA verification widget (new — was missing in v1.0)
Implements the onboarding step from UC-1 / SRS §3.1.1 ("Add/Verify ABHA ID step, using the ABDM Sandbox widget").
- Presented as a distinct step card, not a plain form field, since it is a third-party handoff (opens the ABDM Sandbox widget).
- States: `Not linked` (ink-500, neutral) → `Verifying` (ochre, pending) → `Verified` (sage, with the last-4-digits of the ABHA number shown in `data` mono, never the full number) → `Failed` (brick, with a retry action).
- Must display a small `harbor-100`-background note clarifying sandbox/synthetic-data status per SRS §2.7.2, e.g. "Sandbox environment — test identity, not linked to your real ABHA record." Omitting this note is a compliance-honesty issue, not just a copy nicety.

### 5.13 Critical-info panel (new — was missing in v1.0)
Implements the sequence diagram's requirement that critical highlights (allergies, chronic conditions, recent events) are fetched and rendered *before* the rest of the timeline, in the clinician view.
- Fixed panel, pinned to the top of the clinician record view, `brick-100` background **only if** an allergy is present (otherwise `paper-sunken`), never a full alert-red block.
- Content order is fixed: allergies first, then chronic conditions, then most recent event. Do not reorder based on data volume.
- This panel has no "collapse" affordance — collapsing critical clinical info by default is a safety anti-pattern in a time-pressured clinician workflow.

### 5.14 Role badges — all four roles (v1.0 only defined 2 of 4)
| Role | Badge style |
|---|---|
| Patient | `badge-bloom` (`bloom-200` bg / `bloom-700` text) |
| Clinician | `badge-harbor` (`harbor-100` bg / `harbor-900` text) |
| Provider Staff | `badge-ochre-neutral`: `ochre-100` bg / `ochre-700` text — reuses ochre not as a warning here but as "external actor," distinguished from the warning usage by always pairing with a building/institution icon, never a triangle |
| Administrator | `badge-ink`: `paper-sunken` bg / `ink-900` text, 1px `line-strong` border — deliberately the most muted badge, reflecting the restricted/background nature of admin access to medical content (SRS §2.1) |

### 5.15 Form field — error state (new — was missing in v1.0)
- Border becomes `brick-500` (1.5px), background stays `paper-sunken` (do not tint the field background red — too alarming for a records app, consistent with the alert-banner rule in §5).
- Error text appears **below** the field in `brick-700`, `body-sm`, prefixed with a small brick-colored triangle icon — never color alone (§1.4 rule applies to form validation too).
- Focus ring on an errored field is still `harbor-500` (focus state and error state are visually distinct signals; do not let the error red override the focus indicator).

---

## 6. Shadows (neutral only, never colored)
| Token | Value |
|---|---|
| `shadow-sm` | `0 1px 2px rgba(33,31,27,0.06)` |
| `shadow-md` | `0 4px 12px rgba(33,31,27,0.08)` |
| `shadow-lg` | `0 12px 32px rgba(33,31,27,0.10)` |

---

## 7. Grain / paper texture

- Applied **only** to large background fields (`paper` background), never on top of text, small components, icons, or inside data tables.
- Implementation: SVG `feTurbulence` (`baseFrequency` ~0.85, `numOctaves` 2) as a fixed, non-scrolling overlay, `opacity: 0.035–0.05`, `mix-blend-mode: multiply`.
- Purpose: softens the "sterile SaaS dashboard" feeling without resorting to a gradient or an illustration. It should be felt, not seen — if a reviewer notices "there's a texture," dial opacity down.

---

## 8. Accessibility floor (non-negotiable, this is a healthcare product)

- Body text contrast ≥ 4.5:1 against its background at all times (`ink-700` on `paper`/`paper-raised` clears this comfortably; verify any new pairing). Aim for AAA (7:1) where feasible, matching the aspiration stated by NHS Digital's own service manual (see §11).
- Large text/icons (18px+/bold 14px+) ≥ 3:1.
- Every semantic state = color **+** icon **+** text label, never color alone.
- Visible focus ring on every interactive element: 2px `harbor-500` outline, 2px offset — never remove `:focus-visible` styling, including on error-state fields (§5.15).
- Minimum tap target 44×44px on any touch surface (patient/clinician mobile web).
- Respect `prefers-reduced-motion`: the Continuity Thread may fade in but must not animate/pulse continuously.
- Prefer lists and short paragraphs over dense prose blocks for patient-facing medical content — patients read this while anxious or distracted; do not require them to parse a paragraph to find one fact.

---

## 9. Do / Don't checklist (run this before shipping any screen)

**Do**
- Lead every screen's chrome with `harbor-700`/`harbor-500`; treat Bloom as a spice.
- Use Faustina only where the product should sound like a reassuring person (empty states, onboarding, section headers on marketing/about surfaces).
- Keep the grain texture on background fields only, at low opacity.
- Show data provenance (`sourceProviderId`, `isMock` where relevant) in mono type near any imported record, per SRS §6.3's honesty-about-sandbox-data principle.
- Pair every status color with an icon and a label.
- Use the dotted Continuity Thread for chronology, and only for chronology, with the exact 10px node geometry in §5.8.
- Label every insight/chart "Informational · Not a diagnosis" per §5.11 — this is a compliance requirement, not a style option.
- Show superseded record versions de-emphasized but never hidden or struck through (§5.9).

**Don't**
- Don't add a gradient, blur panel, or colored glow "to make it pop."
- Don't use Inter, Roboto, Arial, Public Sans, or system-ui as the UI font — Elms Sans is the contract (§2.0).
- Don't use Fraunces anywhere — Faustina replaced it system-wide (§2.0).
- Don't put Faustina on a button, a table, or a form label.
- Don't let Bloom pink become a second primary color or a status color.
- Don't use a padlock for consent (§4.2) or a map-pin for provenance (§4.3) — both are specified, redraw if your output drifts toward either.
- Don't fill a destructive action solid on first interaction — require a confirm step.
- Don't use pure `#000`/`#FFF` as a text/background pair, or any neon/saturated hue.
- Don't apply the grain texture to text, icons, tables, or small components.
- Don't tint an error-state field's background red — border + icon + text only (§5.15).
- Don't collapse the clinician critical-info panel by default (§5.13) — it is a safety pattern, not a UI convenience.

---

## 10. Quick reference — CSS custom properties

```css
:root {
  /* neutrals */
  --paper: #F6F4EF;
  --paper-raised: #FFFFFF;
  --paper-sunken: #EFEBE3;
  --ink-900: #211F1B;
  --ink-700: #4A453E;
  --ink-500: #756F65;
  --ink-300: #A39C90;
  --line: #E2DCD0;
  --line-strong: #C9C1B2;

  /* harbor (primary) */
  --harbor-900: #1F4552;
  --harbor-700: #2F5D68;
  --harbor-500: #5B8998;
  --harbor-200: #C6DEE2;
  --harbor-100: #E7F1F2;

  /* bloom (secondary/accent) */
  --bloom-700: #A85468;
  --bloom-500: #C97B8B;
  --bloom-200: #F0D3D9;
  --bloom-100: #FAECEE;

  /* semantic */
  --sage-700: #3F6E52;  --sage-500: #5B8C6E;  --sage-100: #E4EFE6;
  --ochre-700: #8A5A17; --ochre-500: #C1873A; --ochre-100: #F5E8D3;
  --brick-700: #8C2E26; --brick-500: #C1443A; --brick-100: #F5DEDB;

  /* type */
  --font-display: 'Faustina', Georgia, 'Iowan Old Style', serif;
  --font-body: 'Elms Sans', -apple-system, 'Segoe UI', sans-serif;
  --font-mono: 'IBM Plex Mono', ui-monospace, monospace;

  /* radius */
  --radius-sm: 8px; --radius-md: 12px; --radius-lg: 20px; --radius-pill: 999px;

  /* shadow */
  --shadow-sm: 0 1px 2px rgba(33,31,27,0.06);
  --shadow-md: 0 4px 12px rgba(33,31,27,0.08);
  --shadow-lg: 0 12px 32px rgba(33,31,27,0.10);

  /* thread node geometry */
  --thread-node-core: 6px;
  --thread-node-ring: 2px;
}
```

---

## 11. Research grounding (what this system was checked against)

- **NHS Digital Service Manual** (service-manual.nhs.uk): uses a tinted grey background rather than pure white for body content specifically because full white is harder to read for some users (the manual cites the British Dyslexia Association's style-guide recommendation of dark text on a light-but-not-white background) — this directly corroborates Pulse's `paper` (`#F6F4EF`) over-white decision rather than it being an aesthetic-only choice. NHS also enforces WCAG 2.2 AA as a floor with AAA as an explicit aspiration, and repeats the "do not rely on color or position alone" rule across its accessibility guidance — both are now stated as hard rules in §1.4 and §8 above rather than implied.
- **ABDM (Ayushman Bharat Digital Mission) Sandbox conventions**: informed §5.12's ABHA widget spec directly from the SRS's own description of the M1-scoped sandbox flow — the "synthetic test identity, not production" disclosure requirement comes from SRS §2.7.2, not invented.
- This is a design-system-level check, not a full competitive audit. If you are extending this system further, the NHS service manual's component library (`service-manual.nhs.uk/design-system/components`) is the most directly comparable public reference for a patient-facing health record product and is worth a deeper pass before adding net-new patterns (e.g. search, filters, forms) not already specified here.

---

*End of spec. If extending this system (new component, new screen), derive every value from the tokens above — do not introduce a new hex, font, or radius without adding it here first.*
