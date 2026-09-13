// Session/role wire types (issue #55 — client-side admin route gating).
//
// Hand-mirrored from `backend/app/modules/auth/schemas.py` `MeResponse` and
// `backend/app/core/authz.py` `Role` — same precedent as `lib/records.ts`:
// no OpenAPI-to-TypeScript generation set up yet.

export const ROLES = ["PATIENT", "CLINICIAN", "PROVIDER_STAFF", "ADMINISTRATOR"] as const;
export type Role = (typeof ROLES)[number];

export interface Me {
  userId: string;
  role: Role;
  email: string;
  emailVerified: boolean;
}
