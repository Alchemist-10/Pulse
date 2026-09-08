// Typography — docs/design-direction.md, Option A:
//   Noto Sans (Latin + digits) · Noto Sans Devanagari · Noto Sans Tamil ·
//   Noto Sans Malayalam.
//
// Self-hosted via @fontsource (woff2 bundled in node_modules) — no Google Fonts
// hotlink, so the offline demo renders Devanagari from a real bundled face and
// never falls back silently to whatever the OS has.
//
// Weights pinned to 400 / 500 / 700 only. Requesting a full variable range is
// the difference between ~94 KB and ~258 KB on the page a patient loads over a
// bad connection (design-direction.md).
//
// The Latin face carries `tnum`; the family order in --font-sans (tokens.css)
// puts it first so lab tables get tabular figures without a second font.

import "@fontsource/noto-sans/400.css";
import "@fontsource/noto-sans/500.css";
import "@fontsource/noto-sans/700.css";

import "@fontsource/noto-sans-devanagari/400.css";
import "@fontsource/noto-sans-devanagari/500.css";
import "@fontsource/noto-sans-devanagari/700.css";

import "@fontsource/noto-sans-tamil/400.css";
import "@fontsource/noto-sans-tamil/500.css";
import "@fontsource/noto-sans-tamil/700.css";

import "@fontsource/noto-sans-malayalam/400.css";
import "@fontsource/noto-sans-malayalam/500.css";
import "@fontsource/noto-sans-malayalam/700.css";
