# Locale review status

Per this project's own learned rule — "never state an unverified external
fact... record as unverified rather than smoothing it over" — the status of
each non-English locale is stated plainly here rather than assumed correct
because the build passes.

There is no native Hindi, Tamil or Malayalam speaker on this team or
available to this session. All three catalogs were machine/LLM-translated.

| Locale | Status |
|---|---|
| Hindi (`hi`) | **Not reviewed by a native speaker.** Machine/LLM-translated and internally consistency-checked only: the build passes, `next-intl`'s missing-key check (throws in dev/CI) is clean, and translations were done directly against source English strings. |
| Tamil (`ta`) | **Not reviewed by a native speaker.** Machine/LLM-translated, using the Hindi catalog as a meaning reference (`feat(i18n): fill Tamil catalogs`), then consistency-checked the same way as Hindi: no missing keys, build green. |
| Malayalam (`ml`) | **Not reviewed by a native speaker.** Same method as Tamil — machine/LLM-translated using Hindi as the meaning reference (`feat(i18n): fill Malayalam catalogs`), no missing keys, build green. |

"Internally consistency-checked" means: every key present in `en/*.json`
has a corresponding non-empty value in the other three locales, and
`next-intl` fails the build (per `frontend.md`) if that's not true. It does
**not** mean anyone has confirmed the Tamil or Malayalam text reads
naturally, uses locally appropriate register, or avoids a translation that
is technically correct but not what a clinician's or patient's app would
actually say in that language.

Clinical content itself is never translated in any locale, by design (see
`docs/adr/0013-error-codes-not-messages.md` and the "interface is
localised; clinical data is not" rule) — the review gap above is scoped
entirely to UI copy: labels, buttons, error messages, notification text.

## Concrete open items for a real reviewer

Two specific judgment calls were made without a native speaker to check
them, both flagged at the time they were made rather than smoothed over:

1. **Consent-cancel wording.** The "cancel" action on the consent-grant
   form is translated as a "go back" phrase rather than a literal
   "cancel" — Hindi `वापस जाएं`, Tamil `திரும்பு`, Malayalam `മടങ്ങുക`
   (`frontend/src/i18n/messages/{hi,ta,ml}/consent.json`, key
   `consent.new.cancel`). This reads naturally in English UI convention
   ("go back" vs. "cancel out of this form") but a native speaker should
   confirm the same framing lands the same way in each language, rather
   than reading as an odd literal-navigation label where a plain "Cancel"
   might have been expected.

2. **High/low lab-flag abbreviation.** The timeline's abnormal-result
   badges use single-character abbreviations for "high" and "low" —
   Hindi `उ`/`नि`, Tamil `உ`/`தா`, Malayalam `ഉ`/`താ`
   (`frontend/src/i18n/messages/{hi,ta,ml}/timeline.json`, keys
   `timeline.flags.high`/`timeline.flags.low`). Single-letter medical
   abbreviations are a compact convention borrowed from the English "H"/"L"
   pattern common on lab reports; whether a one-character abbreviation
   reads as unambiguous (vs. needing two characters, or a short word) in
   each script is exactly the kind of call that needs a native reader,
   not a translator working from an English reference.

A reviewer should start with these two before doing a general pass, since
they were flagged as judgment calls rather than confirmed translations.
