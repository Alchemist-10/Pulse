import { expect, test } from "@playwright/test";

// Every backend call is mocked here — no FastAPI / Postgres / Redis needed
// (pattern: e2e/timeline.spec.ts). Covers issue #34: entry detail shaped per
// subtype, the abnormal lab marker, and the document viewer.

const BASE = {
  patientId: "22222222-2222-2222-2222-222222222222",
  recordedAt: "2026-08-01T10:05:00Z",
  isCritical: false,
  supersededById: null,
  sourceProviderId: null,
  metadata: {},
  supersedesId: null,
  documents: [] as unknown[],
  codeSystem: null,
  code: null,
  displayName: null,
  valueNumeric: null,
  valueText: null,
  unit: null,
  referenceLow: null,
  referenceHigh: null,
  medicationName: null,
  dosage: null,
  frequency: null,
  route: null,
  text: null,
};

const DIAGNOSIS = {
  ...BASE,
  id: "diag-1",
  entryType: "DIAGNOSIS",
  occurredAt: "2026-08-01T10:00:00Z",
  summary: "Type 2 diabetes mellitus",
  codeSystem: "ICD-10",
  code: "E11",
  displayName: "Type 2 diabetes mellitus",
};

const PRESCRIPTION = {
  ...BASE,
  id: "rx-1",
  entryType: "PRESCRIPTION",
  occurredAt: "2026-07-15T08:00:00Z",
  summary: "Metformin 500mg",
  medicationName: "Metformin",
  dosage: "500mg",
  frequency: "Twice daily",
  route: "Oral",
};

const PROCEDURE = {
  ...BASE,
  id: "proc-1",
  entryType: "PROCEDURE",
  occurredAt: "2026-06-01T08:00:00Z",
  summary: "Appendectomy",
  codeSystem: "ICD-10-PCS",
  code: "0DTJ0ZZ",
  displayName: "Appendectomy",
};

const CLINICAL_NOTE = {
  ...BASE,
  id: "note-1",
  entryType: "CLINICAL_NOTE",
  occurredAt: "2026-05-01T08:00:00Z",
  summary: "Patient reports mild headache.",
  text: "Patient reports mild headache, resolved without medication.",
};

const LAB_NORMAL = {
  ...BASE,
  id: "lab-normal",
  entryType: "LAB_REPORT",
  occurredAt: "2026-08-01T09:00:00Z",
  summary: "Fasting glucose 90 mg/dL",
  codeSystem: "LOINC",
  code: "1558-6",
  displayName: "Fasting glucose",
  valueNumeric: 90,
  unit: "mg/dL",
  referenceLow: 70,
  referenceHigh: 100,
};

const LAB_HIGH = {
  ...LAB_NORMAL,
  id: "lab-high",
  valueNumeric: 150,
  summary: "Fasting glucose 150 mg/dL",
};

const LAB_LOW = {
  ...LAB_NORMAL,
  id: "lab-low",
  valueNumeric: 50,
  summary: "Fasting glucose 50 mg/dL",
};

const DOC_ENTRY = {
  ...BASE,
  id: "doc-entry",
  entryType: "LAB_REPORT",
  occurredAt: "2026-08-01T09:00:00Z",
  summary: "Chest X-ray report",
  codeSystem: "LOINC",
  code: "36643-5",
  displayName: "Chest X-ray",
  documents: [
    {
      id: "doc-pdf",
      entryId: "doc-entry",
      filename: "report.pdf",
      mimeType: "application/pdf",
      sizeBytes: 1234,
      checksumSha256: "abc",
      uploadedAt: "2026-08-01T09:10:00Z",
    },
    {
      id: "doc-png",
      entryId: "doc-entry",
      filename: "scan.png",
      mimeType: "image/png",
      sizeBytes: 5678,
      checksumSha256: "def",
      uploadedAt: "2026-08-01T09:11:00Z",
    },
  ],
};

const ENTRIES: Record<string, unknown> = {
  [DIAGNOSIS.id]: DIAGNOSIS,
  [PRESCRIPTION.id]: PRESCRIPTION,
  [PROCEDURE.id]: PROCEDURE,
  [CLINICAL_NOTE.id]: CLINICAL_NOTE,
  [LAB_NORMAL.id]: LAB_NORMAL,
  [LAB_HIGH.id]: LAB_HIGH,
  [LAB_LOW.id]: LAB_LOW,
  [DOC_ENTRY.id]: DOC_ENTRY,
};

// A 1x1 transparent PNG and a minimal PDF header — the viewer only needs a
// blob it can hand to <img>/<iframe>, not a fully valid rendered document.
const PNG_BYTES = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);
const PDF_BYTES = Buffer.from("%PDF-1.4\n%mock\n", "utf-8");

function mockRoutes(page: import("@playwright/test").Page) {
  return page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const json = (status: number, body: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

    const entryMatch = url.pathname.match(/\/entries\/([^/]+)$/);
    if (entryMatch) {
      const entry = ENTRIES[entryMatch[1]];
      if (entry) return json(200, entry);
      return json(404, { error: { code: "NOT_FOUND", message: "not found" } });
    }

    const docMatch = url.pathname.match(/\/documents\/([^/]+)$/);
    if (docMatch) {
      if (docMatch[1] === "doc-pdf") {
        return route.fulfill({ status: 200, contentType: "application/pdf", body: PDF_BYTES });
      }
      if (docMatch[1] === "doc-png") {
        return route.fulfill({ status: 200, contentType: "image/png", body: PNG_BYTES });
      }
      return json(404, { error: { code: "NOT_FOUND", message: "not found" } });
    }

    return json(404, { error: { code: "NOT_FOUND", message: "not found" } });
  });
}

test("entry detail renders Diagnosis fields", async ({ page }) => {
  await mockRoutes(page);
  await page.goto(`/en/timeline/${DIAGNOSIS.id}`);
  await expect(page.getByText("Type 2 diabetes mellitus").first()).toBeVisible();
  await expect(page.getByText(/ICD-10 E11/)).toBeVisible();
});

test("entry detail renders Prescription fields", async ({ page }) => {
  await mockRoutes(page);
  await page.goto(`/en/timeline/${PRESCRIPTION.id}`);
  await expect(page.getByText("Metformin", { exact: true })).toBeVisible();
  await expect(page.getByText("500mg")).toBeVisible();
  await expect(page.getByText("Twice daily")).toBeVisible();
  await expect(page.getByText("Oral")).toBeVisible();
});

test("entry detail renders Procedure fields", async ({ page }) => {
  await mockRoutes(page);
  await page.goto(`/en/timeline/${PROCEDURE.id}`);
  await expect(page.getByText("Appendectomy").first()).toBeVisible();
});

test("entry detail renders Clinical Note text", async ({ page }) => {
  await mockRoutes(page);
  await page.goto(`/en/timeline/${CLINICAL_NOTE.id}`);
  await expect(
    page.getByText("Patient reports mild headache, resolved without medication."),
  ).toBeVisible();
});

test("entry detail renders Lab Report value, unit and reference range", async ({ page }) => {
  await mockRoutes(page);
  await page.goto(`/en/timeline/${LAB_NORMAL.id}`);
  await expect(page.getByText(/90 mg\/dL/)).toBeVisible();
  await expect(page.getByText(/70 – 100 mg\/dL/)).toBeVisible();
  // In range: no abnormal marker.
  await expect(page.getByText("above range")).not.toBeVisible();
  await expect(page.getByText("below range")).not.toBeVisible();
});

test("abnormal high lab value shows triangle, letter H and the words", async ({ page }) => {
  await mockRoutes(page);
  await page.goto(`/en/timeline/${LAB_HIGH.id}`);
  await expect(page.getByText("▲")).toBeVisible();
  await expect(page.getByText("H", { exact: true })).toBeVisible();
  await expect(page.getByText("above range")).toBeVisible();
});

test("abnormal low lab value shows triangle, letter L and the words", async ({ page }) => {
  await mockRoutes(page);
  await page.goto(`/en/timeline/${LAB_LOW.id}`);
  await expect(page.getByText("▼")).toBeVisible();
  await expect(page.getByText("L", { exact: true })).toBeVisible();
  await expect(page.getByText("below range")).toBeVisible();
});

test("document viewer previews a PDF and a PNG inline", async ({ page }) => {
  await mockRoutes(page);
  await page.goto(`/en/timeline/${DOC_ENTRY.id}`);

  const pdfRow = page.locator("li", { hasText: "report.pdf" });
  await pdfRow.getByRole("button", { name: "View" }).click();
  await expect(pdfRow.locator("iframe")).toBeVisible();

  const pngRow = page.locator("li", { hasText: "scan.png" });
  await pngRow.getByRole("button", { name: "View" }).click();
  await expect(pngRow.locator("img")).toBeVisible();
});
