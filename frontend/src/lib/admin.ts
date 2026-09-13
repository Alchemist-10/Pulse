// Admin wire types (issue #55).
//
// Hand-mirrored from `backend/app/modules/admin/schemas.py` — same
// precedent as `lib/records.ts`: no OpenAPI-to-TypeScript generation set up
// yet. `AdminPatientIdentity` carries identity fields and an entry *count*
// only — never entry content (ADR-0007/ADR-0011). This is a hard rule: any
// screen rendering this type must not fetch or display clinical content for
// the ids it names.

export interface AdminPatientIdentity {
  id: string;
  fullName: string;
  dateOfBirth: string | null;
  phone: string | null;
  claimed: boolean;
  entryCount: number;
}

export interface DuplicateReviewCandidate {
  id: string;
  patientA: AdminPatientIdentity;
  patientB: AdminPatientIdentity;
  score: number;
  status: string;
}

export interface NotDuplicateRequest {
  patientIdA: string;
  patientIdB: string;
}

export interface MergeRequest {
  winnerPatientId: string;
  loserPatientId: string;
}

export interface MergeResult {
  id: string;
  winnerPatientId: string;
  loserPatientId: string;
  occurredAt: string;
  reversedAt: string | null;
}
