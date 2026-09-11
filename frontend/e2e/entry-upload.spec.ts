import { expect, test } from "@playwright/test";

// Every backend call is mocked here — no FastAPI / Postgres / Redis needed
// (pattern: e2e/timeline.spec.ts). Covers issue #34: field-level validation
// from the error envelope's `details` array, and explicit 413 handling.

const PATIENT_ID = "22222222-2222-2222-2222-222222222222";

async function fillCommonFields(page: import("@playwright/test").Page) {
  await page.getByLabel("Patient ID").fill(PATIENT_ID);
  await page.getByRole("combobox", { name: "Entry type" }).click();
  await page.getByRole("option", { name: "Diagnosis" }).click();
  await page.locator('input[type="datetime-local"]').fill("2026-08-01T10:00");
  await page.getByLabel("Code system").fill("ICD-10");
  await page.getByLabel("Code", { exact: true }).fill("E11");
}

test("a stubbed 422 highlights the right field from the details array", async ({ page }) => {
  await page.route("**/api/v1/patients/**/entries", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    await route.fulfill({
      status: 422,
      contentType: "application/json",
      body: JSON.stringify({
        error: {
          code: "VALIDATION_ERROR",
          message: "Validation failed.",
          details: [{ field: "body.displayName", code: "missing" }],
        },
      }),
    });
  });

  await page.goto("/en/timeline/new");
  await fillCommonFields(page);
  await page.getByRole("button", { name: "File entry" }).click();

  const displayNameField = page.getByLabel("Display name");
  await expect(displayNameField).toHaveAttribute("aria-invalid", "true");
  await expect(page.getByText("This field is required.")).toBeVisible();

  // Only the field named in `details` is flagged.
  await expect(page.getByLabel("Code system")).not.toHaveAttribute("aria-invalid", "true");
});

test("a stubbed 413 on document upload shows the size-specific message", async ({ page }) => {
  await page.route("**/api/v1/patients/**/entries", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({ id: "new-entry-1" }),
    });
  });
  await page.route("**/api/v1/patients/**/entries/**/documents", async (route) => {
    await route.fulfill({
      status: 413,
      contentType: "application/json",
      body: JSON.stringify({
        error: {
          code: "PAYLOAD_TOO_LARGE",
          message: "The file exceeds the upload size limit.",
          details: [],
        },
      }),
    });
  });

  await page.goto("/en/timeline/new");
  await fillCommonFields(page);
  await page
    .locator('input[type="file"]')
    .setInputFiles({ name: "report.pdf", mimeType: "application/pdf", buffer: Buffer.from("%PDF-1.4") });
  await page.getByRole("button", { name: "File entry" }).click();

  await expect(
    page.getByText("This file is too large — compress or split it and try again."),
  ).toBeVisible();
});
