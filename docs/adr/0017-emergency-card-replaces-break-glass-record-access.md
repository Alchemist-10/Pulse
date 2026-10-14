---
status: accepted
---

# Emergency card replaces break-glass record access

Break-glass previously opened a Patient's whole record to a Clinician for 60 minutes. It now reveals only the Patient's **emergency card**: a short summary the Patient writes and controls (blood type, allergies, conditions, medications, next of kin, notes), each field individually shareable. Break-glass still requires a justification, is audited as `BREAK_GLASS_ACCESS`, and notifies the Patient. It no longer contributes to `accessible_entries`.

## Card access

- The Patient may generate, rotate or disable a QR token. The QR encodes a link carrying an unguessable token; any signed-in Patient, Clinician or Provider Staff member who opens it sees the card. Administrators never can.
- Every non-owner view emits one `EMERGENCY_CARD_VIEWED` audit event and a mandatory notification. Neither carries card contents.
- Fields marked hidden are never sent; they are `null` on the wire.
- Card text is stored in dedicated columns, typed by the Patient, never copied from Medical Entries and never JSONB.
- The token is stored in plain text (not hashed) so the Patient can re-display the QR. It is a revocable capability for non-record data, behind login and audit; rotation invalidates it immediately.

## Consent expiry

Consent expiry is optional. `NULL` means live until revoked. Revocation remains immediate and uncached.

## Consequences

A Clinician needing records in an emergency now needs consent; the card carries what is safe to share without it. Superseded: the unscoped break-glass read rule in `domain-model.md`.
