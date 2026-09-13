// Analytics wire types (issue #55).
//
// Hand-mirrored from `backend/app/modules/analytics/schemas.py` and the
// series shapes it reuses from `backend/app/modules/records/schemas.py`
// (`LabTrendPoint`, `MonthlyVisitCount`, `MedicationSummary`,
// `ProviderEntryCount`) — same precedent as `lib/records.ts`: no
// OpenAPI-to-TypeScript generation set up yet.

/** One point in a lab/vital-sign trend. `isAbnormal` is set by the backend
 * service against the row's own reference bounds — never recomputed here. */
export interface LabTrendPoint {
  occurredAt: string;
  valueNumeric: number | null;
  valueText: string | null;
  unit: string | null;
  referenceLow: number | null;
  referenceHigh: number | null;
  isAbnormal: boolean | null;
}

export interface MonthlyVisitCount {
  month: string;
  count: number;
}

/** One active-medication row. `medicationName`, `dosage`, `frequency`, `route`
 * are clinical content — always rendered via `ClinicalText`, never
 * translated (.claude/rules/clinical-safety.md). */
export interface MedicationSummary {
  occurredAt: string;
  medicationName: string;
  dosage: string | null;
  frequency: string | null;
  route: string | null;
}

export interface ProviderEntryCount {
  providerId: string | null;
  count: number;
}

/** The five informational data-quality flags (never blocking) named in
 * `backend/app/modules/analytics/schemas.py` `DataQualityFlag`. */
export const DATA_QUALITY_FLAGS = [
  "MISSING_DOB",
  "MISSING_CONTACT",
  "FUTURE_DATED_ENTRY",
  "IMPLAUSIBLE_DOB",
  "UNCLAIMED_LONG_LIVED",
] as const;
export type DataQualityFlag = (typeof DATA_QUALITY_FLAGS)[number];
