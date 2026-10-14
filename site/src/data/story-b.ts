// Chapter flow facts are checked against the implementation on 2026-10-15.
// Consent lifecycle: backend/app/modules/consent/service.py:111-185,
// backend/app/modules/consent/models.py:27-81, docs/workflows/README.md:73-81.
export const stages = [
  // Consent and derived permission are written together: backend/app/modules/consent/service.py:111-150.
  {
    state: "Consent recorded",
    permission: "Live permission: active",
    note: "The Patient selects an individual Clinician, entry types, an optional clinical-date window, purpose and expiry.",
  },
  // Record reads are filtered then audited: backend/app/modules/records/service.py:132-169.
  {
    state: "Filtered request",
    permission: "Only rows in scope are returned",
    note: "Each clinical read is filtered by live permission. The read is audited as one request, with access metadata rather than record contents.",
  },
  // Revoke removes the live permission and sends a mandatory notice: backend/app/modules/consent/service.py:153-185.
  {
    state: "Permission removed",
    permission: "Next request: denied",
    note: "Revocation stamps the Consent and removes its derived permission in the same transaction. The grantee is notified.",
  },
] as const;
