import { expect, test } from "@playwright/test";

// Phase 4 screens (issue #56 acceptance: "touch the new Phase 4 screens").
// Every backend call is mocked here, same pattern as the rest of e2e/.

const PATIENT_ID = "66666666-6666-6666-6666-666666666666";

test("analytics screen renders visit frequency and data-quality flags", async ({ page }) => {
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const json = (status: number, body: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

    if (url.pathname.endsWith("/patients/me")) {
      return json(200, { id: PATIENT_ID, fullName: "Arjun Pillai", claimed: true });
    }
    if (url.pathname === `/api/v1/patients/${PATIENT_ID}/analytics/visit-frequency`) {
      return json(200, [{ month: "2026-07", count: 2 }]);
    }
    if (url.pathname === `/api/v1/patients/${PATIENT_ID}/analytics/active-medications`) {
      return json(200, []);
    }
    if (url.pathname === `/api/v1/patients/${PATIENT_ID}/analytics/provider-entry-counts`) {
      return json(200, []);
    }
    if (url.pathname === `/api/v1/patients/${PATIENT_ID}/analytics/data-quality-flags`) {
      return json(200, ["MISSING_CONTACT"]);
    }
    if (url.pathname === `/api/v1/patients/${PATIENT_ID}/entries`) {
      return json(200, { items: [], nextCursor: null });
    }
    return json(404, { error: { code: "NOT_FOUND", message: "not found" } });
  });

  await page.goto("/en/analytics");
  await expect(page.getByRole("heading", { name: "Your health analytics" })).toBeVisible();
  await expect(page.getByText("No contact phone number is on file for you.")).toBeVisible();
});

test("admin dashboard denies a non-Administrator and admits one", async ({ page }) => {
  await page.route("**/api/v1/auth/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        userId: "u-1",
        role: "PATIENT",
        email: "not-admin@example.com",
        emailVerified: true,
      }),
    });
  });

  await page.goto("/en/admin");
  await expect(page.getByText("Administrator access required")).toBeVisible();
  await expect(page.getByText("This screen is for Administrators only.")).toBeVisible();

  await page.route(
    "**/api/v1/auth/me",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          userId: "u-2",
          role: "ADMINISTRATOR",
          email: "admin@example.com",
          emailVerified: true,
        }),
      });
    },
    { times: 1 },
  );

  await page.reload();
  await expect(page.getByRole("heading", { name: "Admin dashboard" })).toBeVisible();
  await expect(page.getByText("Duplicate review")).toBeVisible();
});

test("admin duplicate review lists a candidate and merges it", async ({ page }) => {
  const CANDIDATE_ID = "cand-1";
  const mergedItems: string[] = [];

  await page.route("**/api/v1/**", async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const json = (status: number, body: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

    if (url.pathname.endsWith("/auth/me")) {
      return json(200, {
        userId: "u-admin",
        role: "ADMINISTRATOR",
        email: "admin@example.com",
        emailVerified: true,
      });
    }
    if (url.pathname === "/api/v1/admin/duplicate-review") {
      const items = mergedItems.includes(CANDIDATE_ID)
        ? []
        : [
            {
              id: CANDIDATE_ID,
              score: 0.91,
              patientA: {
                id: "pat-a",
                fullName: "Anand Kumar",
                dateOfBirth: "1980-01-01",
                phone: "9876543210",
                claimed: true,
                entryCount: 5,
              },
              patientB: {
                id: "pat-b",
                fullName: "Anand  Kumar",
                dateOfBirth: "1980-01-01",
                phone: "9876543210",
                claimed: false,
                entryCount: 1,
              },
            },
          ];
      return json(200, items);
    }
    if (url.pathname === "/api/v1/admin/duplicate-review/merge" && req.method() === "POST") {
      mergedItems.push(CANDIDATE_ID);
      return json(200, {
        id: "merge-1",
        occurredAt: "2026-09-01T00:00:00Z",
        reversedAt: null,
      });
    }
    return json(404, { error: { code: "NOT_FOUND", message: "not found" } });
  });

  await page.goto("/en/admin/duplicates");
  await expect(page.getByRole("heading", { name: "Duplicate review" })).toBeVisible();
  await expect(page.getByText("Anand Kumar")).toBeVisible();

  await page.getByRole("button", { name: "Merge" }).click();
  await expect(page.getByText("No duplicate candidates are waiting for review.")).toBeVisible();
  await expect(page.getByText("Merges this session")).toBeVisible();
});
