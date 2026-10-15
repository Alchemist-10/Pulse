import { expect, test } from "@playwright/test";

// Patient asks a rule-based question and sees a typed answer plus the receipt.
// Every backend call is mocked (pattern: e2e/emergency-card.spec.ts).
test("patient asks for a lab value and can open the receipt", async ({ page }) => {
  let asked: Record<string, unknown> | null = null;

  await page.route("**/api/v1/**", async (route) => {
    const req = route.request();
    const path = new URL(req.url()).pathname;
    const json = (body: unknown) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(body),
      });
    if (path.endsWith("/auth/me"))
      return json({ userId: "p1", email: "p@example.com", role: "PATIENT", emailVerified: true });
    if (path.endsWith("/api/v1/ask")) {
      asked = req.postDataJSON() as Record<string, unknown>;
      return json({
        intent: "LATEST_LAB",
        blocks: [
          {
            kind: "lab_value",
            testName: "Hemoglobin A1c",
            valueNumeric: "7.8",
            valueText: null,
            unit: "%",
            referenceLow: "4.0",
            referenceHigh: "5.6",
            isAbnormal: true,
            observedAt: "2026-10-01T00:00:00Z",
          },
        ],
        receipt: {
          filter: "accessible_entries",
          entryIds: [],
          entryCount: 3,
          auditLogged: true,
        },
      });
    }
    return json({ items: [], nextCursor: null });
  });

  await page.goto("/en/ask");
  await page.getByLabel("Your question").fill("What is my latest HbA1c?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();

  await expect(page.getByText("Hemoglobin A1c")).toBeVisible();
  await expect(page.getByText("Outside reference range")).toBeVisible();
  expect(asked).toMatchObject({ question: "What is my latest HbA1c?", locale: "en" });

  await page.getByText("Show your work").click();
  await expect(
    page.getByText("Your medical entries, through the consent filter"),
  ).toBeVisible();
  await expect(page.getByText("Entries used: 3")).toBeVisible();
});
