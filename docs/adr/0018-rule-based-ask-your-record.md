---
status: accepted
---

# Ask your record is rule-based, stateless and audited

Patients can ask free-text questions about their own record. Answers come from a deterministic intent matcher and fixed queries, not a language model.

## Decision

- A question maps to one of eight intents (latest lab, lab trend, medications, allergies, conditions, what changed, who accessed, emergency preview) by per-locale phrase lexicons plus stdlib `difflib` fuzzy matching. Anything else returns `UNMATCHED` and suggestion chips.
- Every clinical read goes through existing services, so `accessible_entries` applies exactly as on the timeline. The module owns no tables and writes no SQL.
- The patient is resolved from the session. A request cannot name another Patient. Non-patients, administrators included, get 404.
- Answers are typed blocks. Interface text is a catalog key; clinical values are returned verbatim and rendered in `ClinicalText`.
- Nothing is persisted: no chat history, no question text. A stored answer would be a copy of the record outside the consent filter.
- One `ANALYTICS_VIEWED` audit event per answered question, with `intent` and a row count in metadata. Never the question, the matched test name or any value. Unmatched questions read nothing and log nothing.
- Each answer carries a receipt: what it was read from, how many entries, and that it was logged.
- "Who accessed my records" reads the existing audit projection and drops the patient's own events.
- Allergies are read from the emergency card; there is no allergy Medical Entry type.

## Consequences

- Coverage is bounded by the lexicons. Hindi, Tamil and Malayalam lexicons and catalogs are unreviewed (`docs/locale-review.md`).
- "What changed" approximates "since last visit" as entries recorded in a 7, 30 or 90 day window. There is no visit entity.
- Timeline-backed intents also produce the records module's own `ENTRY_VIEWED` event, so those questions log two events for two real reads.
- An LLM could later rephrase answers, never retrieve them.
