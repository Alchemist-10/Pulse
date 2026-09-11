// Records wire types (timeline screen, issue #33; entry detail + document
// upload, issue #34).
//
// Hand-mirrored from `backend/app/modules/records/schemas.py` — the repo has
// no OpenAPI-to-TypeScript generation set up yet (Phase 1 precedent:
// `frontend/src/app/[locale]/profile/page.tsx` does the same for
// PatientProfile). Keep this in sync with `EntrySummary` / `EntryDetail`
// until a generator lands.

import { ApiError, type ApiErrorBody } from "./api";

export const ENTRY_TYPES = [
  "DIAGNOSIS",
  "PRESCRIPTION",
  "LAB_REPORT",
  "PROCEDURE",
  "CLINICAL_NOTE",
] as const;

export type EntryType = (typeof ENTRY_TYPES)[number];

/** One timeline row. Clinical content lives only in `summary` — recorded
 * text, rendered verbatim via `ClinicalText`, never translated. */
export interface EntrySummary {
  id: string;
  patientId: string;
  entryType: EntryType;
  occurredAt: string;
  recordedAt: string;
  isCritical: boolean;
  supersededById: string | null;
  sourceProviderId: string | null;
  summary: string | null;
}

export interface RecordDocument {
  id: string;
  entryId: string;
  filename: string;
  mimeType: string;
  sizeBytes: number;
  checksumSha256: string;
  uploadedAt: string;
}

/** Full entry, including the subtype fields relevant to its `entryType`. */
export interface EntryDetail extends EntrySummary {
  supersedesId: string | null;
  documents: RecordDocument[];
  codeSystem: string | null;
  code: string | null;
  displayName: string | null;
  valueNumeric: number | null;
  valueText: string | null;
  unit: string | null;
  referenceLow: number | null;
  referenceHigh: number | null;
  medicationName: string | null;
  dosage: string | null;
  frequency: string | null;
  route: string | null;
  text: string | null;
}

export interface Page<T> {
  items: T[];
  nextCursor: string | null;
}

/** What a Provider files, or what a correction re-files (`EntryCreate` on the
 * backend). Subtype fields are optional at the wire; the service validates
 * the set required for `entryType`. */
export interface EntryCreate {
  entryType: EntryType;
  occurredAt: string;
  isCritical?: boolean;
  sourceProviderId?: string | null;
  codeSystem?: string | null;
  code?: string | null;
  displayName?: string | null;
  valueNumeric?: number | null;
  valueText?: string | null;
  unit?: string | null;
  referenceLow?: number | null;
  referenceHigh?: number | null;
  medicationName?: string | null;
  dosage?: string | null;
  frequency?: string | null;
  route?: string | null;
  text?: string | null;
}

/** The three MIME types the upload endpoint accepts and the viewer renders
 * (backend `service._MAGIC`, docs/api-conventions.md: MIME allowlist). */
export const VIEWABLE_DOCUMENT_MIME_TYPES = [
  "application/pdf",
  "image/png",
  "image/jpeg",
] as const;

/**
 * Upload a document to an Entry via `XMLHttpRequest` rather than `fetch` —
 * only `XMLHttpRequest` exposes upload progress events, and the upload UI
 * needs a progress bar (issue #34). `onProgress` receives a 0..1 fraction.
 *
 * A 413 is handled explicitly even when the rejecting layer (Caddy's outer
 * body limit, P2.11) sends no JSON envelope at all: the status code alone is
 * enough to synthesize `PAYLOAD_TOO_LARGE` so the caller always gets the
 * specific "too large" message, never a generic failure.
 */
export function uploadDocument(
  patientId: string,
  entryId: string,
  file: File,
  onProgress?: (fraction: number) => void,
): Promise<RecordDocument> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open(
      "POST",
      `/api/v1/patients/${patientId}/entries/${entryId}/documents`,
    );
    xhr.withCredentials = true;

    xhr.upload.onprogress = (event) => {
      if (onProgress && event.lengthComputable) {
        onProgress(event.loaded / event.total);
      }
    };

    xhr.onerror = () => {
      reject(new ApiError(0, { code: "NETWORK", message: "Network error" }));
    };

    xhr.onload = () => {
      let payload: unknown;
      try {
        payload = xhr.responseText ? JSON.parse(xhr.responseText) : undefined;
      } catch {
        payload = undefined;
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(payload as RecordDocument);
        return;
      }

      const envelope = (payload as { error?: ApiErrorBody } | undefined)?.error;
      reject(
        new ApiError(
          xhr.status,
          envelope ?? {
            code: xhr.status === 413 ? "PAYLOAD_TOO_LARGE" : "GENERIC",
            message: `HTTP ${xhr.status}`,
          },
        ),
      );
    };

    const form = new FormData();
    form.append("file", file);
    xhr.send(form);
  });
}
