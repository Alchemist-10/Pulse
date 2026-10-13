# Pulse UI design system — Burgundy Material

<!-- Design authority for the current web UI. Updated 2026-10-13. -->

Pulse is a lifelong health record used by Patients, Clinicians, Provider Staff, and Administrators. The interface must make the medical history, consent, and audit trail feel continuous and trustworthy. Its new visual language combines **burgundy**, **soft neumorphic depth**, **translucent glass**, and **selective clay-like actions**. This document supersedes the visual instructions in `Pulse_design.md` and the options in `docs/design-direction.md`; those files remain as history.

Rendered previews: [desktop](docs/design-preview-desktop.png) · [mobile](docs/design-preview-mobile.png). They show the signed-out home page; the same tokens and components carry the authenticated workspaces.

## Design intent

The product should feel like a carefully made personal record, with calm depth and clear hierarchy. The three material effects have separate jobs:

| Material | Where it belongs | What it communicates |
| --- | --- | --- |
| Glass | App header, mobile task bar, overlays, major overview cards | A light layer above the page; navigation remains in view |
| Neumorphism | Search/filter toolbars, text fields, selects, secondary actions | Recessed inputs and gently raised controls |
| Clay | Primary buttons, brand mark, important empty-state icon | A tactile, unmistakable action or anchor |

Use one dominant material per component. Do not stack nested glass cards or put a translucent surface behind long clinical notes. A table, record detail, or audit entry can use an opaque raised surface for legibility and rendering performance. Shadows explain elevation; borders and labels still define controls when shadows disappear in bright light.

## Color and tokens

`frontend/src/app/globals.css` is the implementation source of truth. Colors use OKLCH to keep lightness predictable. Components consume semantic utilities, never literal colors.

| Token | Light | Dark | Usage |
| --- | --- | --- | --- |
| `--primary` | `oklch(0.405 0.117 8)` | `oklch(0.78 0.091 4)` | Burgundy actions, links, active navigation |
| `--primary-hover` | `oklch(0.35 0.105 8)` | `oklch(0.835 0.075 4)` | Primary hover |
| `--primary-soft` | `oklch(0.926 0.038 7)` | `oklch(0.342 0.052 6)` | Active navigation, icon wells, gentle highlights |
| `--background` | `oklch(0.966 0.009 5)` | `oklch(0.19 0.024 8)` | Warm porcelain page base |
| `--card` | `oklch(0.996 0.003 20)` | `oklch(0.258 0.029 8)` | Opaque reading surface |
| `--foreground` | `oklch(0.252 0.023 5)` | `oklch(0.985 0.001 106.423)` | Primary text |
| `--muted-foreground` | `oklch(0.455 0.023 7)` | `oklch(0.709 0.01 56.259)` | Supporting text |
| `--ring` | `oklch(0.53 0.12 8)` | `oklch(0.78 0.091 4)` | Focus ring |

The page moves from near-white at the top to a very pale burgundy tint below. The gradient is a quiet background, not a content surface. `--glass-fill`, `--glass-border`, `--shadow-card`, `--shadow-raised`, `--shadow-inset`, and `--shadow-clay` define the materials. Dark mode uses its own values; never invert a light shadow or put pure black behind long text.

**Clinical meaning remains separate from branding.** Critical findings, denied access, break-glass use, active consent, and expiry continue to use the existing domain tokens. They always include text and/or an icon. Burgundy must not imply “critical” simply because it is dark red. High and low lab results remain distinguishable by their explicit words and direction indicators.

## Components

| Component | Treatment | Interaction |
| --- | --- | --- |
| App header and mobile task bar | Glass with a visible lower/top edge | Sticky; active destination uses a soft burgundy fill and `aria-current` |
| Primary button | Burgundy clay surface, rounded corners | Hover gains depth; pressed state becomes inset; disabled remains clearly labeled |
| Secondary/outline button | Porcelain raised surface | Hover changes fill; focus ring is independent of shadow |
| Input, textarea, select | Muted recessed well | Focus adds a three-pixel ring; invalid state retains its own semantic color |
| Default card | Opaque raised porcelain surface | Dense clinical and administrative content stays sharp |
| Overview card | Opt-in `material-card` glass surface | Use only for a few high-level or personal panels |
| Clinical list item / audit table | Opaque raised surface | Legibility and scan order take priority over blur |
| Popover, menu, sheet | Glass with solid-enough fill | Content remains readable over any page background |
| Empty state | Spacious glass card with one clay icon | One obvious next action, if available |
| Profile card | Glass body, gentle burgundy header tint, raised avatar | Identity data remains flat and easy to copy |

Use `material-glass`, `material-card`, `material-raised`, `material-inset`, and `material-clay` utility classes. The classes express a surface role, not a page-specific effect. New components should use existing shadcn primitives where possible; a custom clinical state must keep its semantic token and redundant cue.

## Layout and typography

- Keep the existing Noto Sans family for English, Hindi, Tamil, and Malayalam. It supports the four shipped locales and tabular numerals in the current app; a Latin-only display font would fragment the interface.
- Page titles lead at `text-2xl` on mobile and `text-3xl` on wider screens. Body copy is at least 14 px; clinical values and form labels remain easy to scan.
- Use a 4 px spacing rhythm. A 16–24 px card inset, 24–32 px section gap, and 44 px minimum touch target provide the default density. Dense clinician tables may be tighter without reducing readable type.
- Main content retains a maximum width of 72 rem. On phones, forms and cards become one column. The patient task bar stays at the bottom with safe-area padding.
- Standard control radius is about 14 px; cards use about 20 px. Avoid turning every clinical item into a pill.

## States, accessibility, and performance

Every interactive element needs a visible keyboard focus state; shadows are never the only indicator. Text must meet WCAG AA contrast (4.5:1 for regular text, 3:1 for large text) in both themes and over the actual rendered glass. Use an opaque fallback when blur is unsupported or `prefers-reduced-transparency` is enabled. Respect `prefers-reduced-motion`; movement is brief and never required to understand an action. Error, loading, empty, selected, disabled, and hover states must preserve their labels and icon cues.

Blur is limited to persistent chrome, overlays, and a few overview surfaces. Repeated clinical rows use `material-raised` without blur so long timelines and audit views remain responsive on mid-range Android devices. Do not put sensitive medical information into decorative imagery or shadow effects. The visual change must not alter access checks, consent wording, or audit behavior.

## Page application

- **Home and login:** glass overview or form cards, one clear clay primary action. The demo-account card is secondary.
- **Profile:** calm identity header, visible avatar, one coherent personal-details card. Keep Patient ID copyable and selectable.
- **Timeline and record details:** burgundy markers and actions; opaque medical-entry rows and readable chronology. Clinical severity remains semantic.
- **Consent and audit:** raised lists with strong status labels. Revocation and break-glass states are explicit, never a merely decorative burgundy treatment.
- **Clinician, analytics, and admin:** denser workspace; neumorphic filters and restrained glass only on chrome or summaries. Tables stay opaque.

## Review checklist

1. Inspect desktop and mobile in both light and dark themes, including long localized labels.
2. Verify contrast, keyboard focus, empty/error/loading states, and the real Patient/Clinician navigation.
3. Check that glass text is readable on the lightest and darkest background positions.
4. Confirm no horizontal overflow at 360 px and no sticky header or task bar obscures content.
5. Run frontend lint, typecheck, locale validation, and the relevant end-to-end smoke tests before merging.
