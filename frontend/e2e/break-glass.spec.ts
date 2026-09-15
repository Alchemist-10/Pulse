import { expect, test } from "@playwright/test";

// Clinician break-glass from the patient-record screen. Every backend call is
// mocked (pattern: e2e/smoke.spec.ts). Entries 404 until the emergency grant
// is requested, then read normally.
const PATIENT_ID = "33333333-3333-3333-3333-333333333333";

const ENTRY = {
  id: "bg1",
  patientId: PATIENT_ID,
  entryType: "DIAGNOSIS",
  occurredAt: "2026-08-01T10:00:00Z",
  recordedAt: "2026-08-01T10:05:00Z",
  isCritical: false,
  supersededById: null,
  sourceProviderId: null,
  summary: "Acute asthma",
};

function mock(page: import("@playwright/test").Page, role: string) {
  let granted = false;
  let justification: string | null = null;
  const notFound = {
    error: { code: "NOT_FOUND", message: "Not found", details: null, requestId: "r" },
  };
  page.route("**/api/v1/**", async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const json = (status: number, body: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

    if (url.pathname.endsWith("/auth/me")) {
      return json(200, { id: "c1", email: "dr@example.com", role, emailVerified: true });
    }
    if (url.pathname === `/api/v1/patients/${PATIENT_ID}/break-glass` && req.method() === "POST") {
      justification = (req.postDataJSON() as { justification: string }).justification;
      granted = true;
      return json(201, {
        id: "g1",
        patientId: PATIENT_ID,
        clinicianUserId: "c1",
        justification,
        grantedAt: "2026-09-15T10:00:00Z",
        expiresAt: "2026-09-15T11:00:00Z",
      });
    }
    if (url.pathname === `/api/v1/patients/${PATIENT_ID}/entries`) {
      return granted ? json(200, { items: [ENTRY], nextCursor: null }) : json(404, notFound);
    }
    return json(404, notFound);
  });
  return { justification: () => justification };
}

test("clinician requests emergency access after a 404 and then reads the record", async ({ page }) => {
  const state = mock(page, "CLINICIAN");
  await page.goto(`/en/patients/${PATIENT_ID}/records`);

  await expect(page.getByText("We could not find that record.")).toBeVisible();
  const submit = page.getByRole("button", { name: "Request emergency access" });
  await submit.click();
  await expect(page.getByText("Enter a justification.")).toBeVisible();
  expect(state.justification()).toBeNull();

  await page.getByLabel("Justification").fill("Unconscious in ED, no consent possible");
  await submit.click();

  await expect(page.getByText("Acute asthma")).toBeVisible();
  expect(state.justification()).toBe("Unconscious in ED, no consent possible");
});

test("provider staff never see the emergency access form", async ({ page }) => {
  mock(page, "PROVIDER_STAFF");
  await page.goto(`/en/patients/${PATIENT_ID}/records`);

  await expect(page.getByText("We could not find that record.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Request emergency access" })).toHaveCount(0);
});
