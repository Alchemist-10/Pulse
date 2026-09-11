import { expect, test } from "@playwright/test";

// Every backend call is mocked here — no FastAPI / Postgres / Redis needed
// (pattern: e2e/smoke.spec.ts).
const PATIENT_ID = "22222222-2222-2222-2222-222222222222";

const FIXTURE_PROFILE = {
  id: PATIENT_ID,
  fullName: "Aarav Menon",
  dateOfBirth: "1990-04-12",
  sex: "Male",
  phone: "9876543210",
  addressLine: "12 MG Road",
  city: "Kochi",
  state: "Kerala",
  localePreference: "en",
  claimed: true,
};

const FIXTURE_ENTRIES = [
  {
    id: "e1",
    patientId: PATIENT_ID,
    entryType: "DIAGNOSIS",
    occurredAt: "2026-08-01T10:00:00Z",
    recordedAt: "2026-08-01T10:05:00Z",
    isCritical: true,
    supersededById: null,
    sourceProviderId: null,
    summary: "Type 2 diabetes mellitus",
  },
  {
    id: "e2",
    patientId: PATIENT_ID,
    entryType: "LAB_REPORT",
    occurredAt: "2026-08-01T09:00:00Z",
    recordedAt: "2026-08-01T09:05:00Z",
    isCritical: false,
    supersededById: null,
    sourceProviderId: null,
    summary: "HbA1c 7.2%",
  },
  {
    id: "e3",
    patientId: PATIENT_ID,
    entryType: "PRESCRIPTION",
    occurredAt: "2026-07-15T08:00:00Z",
    recordedAt: "2026-07-15T08:05:00Z",
    isCritical: false,
    supersededById: null,
    sourceProviderId: null,
    summary: "Metformin 500mg",
  },
];

function mockRoutes(page: import("@playwright/test").Page, entries = FIXTURE_ENTRIES) {
  return page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const json = (status: number, body: unknown) =>
      route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(body),
      });

    if (url.pathname.includes("/patients/me")) return json(200, FIXTURE_PROFILE);
    if (url.pathname.includes(`/patients/${PATIENT_ID}/entries`)) {
      const entryType = url.searchParams.get("entryType");
      const items = entryType ? entries.filter((e) => e.entryType === entryType) : entries;
      return json(200, { items, nextCursor: null });
    }
    return json(404, { error: { code: "NOT_FOUND", message: "not found" } });
  });
}

test("timeline renders the stubbed entries in date order", async ({ page }) => {
  await mockRoutes(page);
  await page.goto("/en/timeline");

  await expect(page.getByRole("heading", { name: "Your timeline" })).toBeVisible();

  const rows = page.locator("li", { has: page.locator("a") });
  await expect(rows).toHaveCount(3);
  // occurredAt desc: diagnosis, then lab report (same day), then prescription.
  await expect(rows.nth(0)).toContainText("Type 2 diabetes mellitus");
  await expect(rows.nth(1)).toContainText("HbA1c 7.2%");
  await expect(rows.nth(2)).toContainText("Metformin 500mg");

  // Critical flag has a text label, never colour alone.
  await expect(rows.nth(0)).toContainText("Critical");
});

test("the entryType filter narrows the list", async ({ page }) => {
  await mockRoutes(page);
  await page.goto("/en/timeline");

  const rows = page.locator("li", { has: page.locator("a") });
  await expect(rows).toHaveCount(3);

  await page.getByRole("combobox", { name: "Filter by type" }).click();
  await page.getByRole("option", { name: "Lab report" }).click();

  await expect(rows).toHaveCount(1);
  await expect(rows.nth(0)).toContainText("HbA1c 7.2%");
  await expect(page.getByText("Type 2 diabetes mellitus")).not.toBeVisible();
});

test("the empty state shows when the stub returns items: []", async ({ page }) => {
  await mockRoutes(page, []);
  await page.goto("/en/timeline");

  await expect(page.getByText("No entries yet", { exact: true })).toBeVisible();
  await expect(page.getByText("Nothing has been filed to your timeline yet.")).toBeVisible();
});
