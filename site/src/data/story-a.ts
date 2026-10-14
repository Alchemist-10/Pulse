// Facts for chapters 1-3 that are not in facts.ts. Checked 2026-10-14.
// Permission enum: backend/app/core/authz.py:18-63. Holders: ROLE_PERMISSIONS, authz.py:66-108.
// Labels paraphrase the comments above each enum member (authz.py:19-63).

type Perm = { id: string; label: string; held: readonly string[] };
export const permissionGroups: { group: string; items: Perm[] }[] = [
  {
    group: "Identity and profile",
    items: [
      { id: "PATIENT_PROFILE_READ_SELF", label: "Read own profile", held: ["PATIENT"] },
      { id: "PATIENT_PROFILE_UPDATE_SELF", label: "Change own interface language", held: ["PATIENT"] },
      { id: "USER_CREDENTIALS_CHANGE", label: "Change own credentials", held: ["PATIENT", "PROVIDER_STAFF", "CLINICIAN", "ADMINISTRATOR"] },
      { id: "PROVIDER_READ", label: "See a provider's public name and city", held: ["PATIENT", "PROVIDER_STAFF", "CLINICIAN", "ADMINISTRATOR"] },
    ],
  },
  {
    group: "Clinical records",
    items: [
      { id: "RECORDS_READ", label: "Read Medical Entries (rows filtered per request)", held: ["PATIENT", "PROVIDER_STAFF", "CLINICIAN"] },
      { id: "RECORDS_WRITE", label: "File entries and attach documents", held: ["PROVIDER_STAFF"] },
    ],
  },
  {
    group: "Consent and emergency access",
    items: [
      { id: "CONSENT_READ_SELF", label: "Review own consents", held: ["PATIENT"] },
      { id: "CONSENT_MANAGE_SELF", label: "Grant and revoke own consents", held: ["PATIENT"] },
      { id: "CONSENT_READ_GRANTED", label: "List patients whose consent names me", held: ["CLINICIAN"] },
      { id: "BREAK_GLASS_REQUEST", label: "Request emergency access with a reason", held: ["CLINICIAN"] },
    ],
  },
  {
    group: "Audit and notifications",
    items: [
      { id: "AUDIT_READ_SELF", label: "Read own audit log", held: ["PATIENT"] },
      { id: "NOTIFICATION_READ_SELF", label: "Read own notifications", held: ["PATIENT"] },
      { id: "NOTIFICATION_PREFERENCES_READ_SELF", label: "Read notification preferences", held: ["PATIENT"] },
      { id: "NOTIFICATION_MANAGE_SELF", label: "Mark read, change preferences", held: ["PATIENT"] },
    ],
  },
  {
    group: "Data quality and administration",
    items: [
      { id: "ANALYTICS_DATA_QUALITY_READ", label: "Read data-quality flags (identity only)", held: ["PATIENT", "ADMINISTRATOR"] },
      { id: "ADMIN_DUPLICATE_REVIEW", label: "Review and merge duplicate patients", held: ["ADMINISTRATOR"] },
    ],
  },
] as const;

/** Matrix column order (matches facts.ts roles) with a short header for narrow screens. */
export const roleColumns = [
  { id: "PATIENT", short: "Patient" },
  { id: "PROVIDER_STAFF", short: "Staff" },
  { id: "CLINICIAN", short: "Clinician" },
  { id: "ADMINISTRATOR", short: "Admin" },
] as const;

export const routeCoverage = {
  declared: 42, // 43 endpoints (facts stats.endpoints) minus the allow-listed GET /api/v1/health: app/main.py:70,75
  allowlisted: "GET /api/v1/health", // backend/tests/test_route_coverage.py:22-24
  testPath: "backend/tests/test_route_coverage.py",
} as const;
