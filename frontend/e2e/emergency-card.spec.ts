import { expect, test } from "@playwright/test";

// Patient edits the emergency card, chooses what is shown, and generates a QR.
// Every backend call is mocked (pattern: e2e/break-glass.spec.ts).
const TOKEN = "AbCdEfGhIjKlMnOpQrStUvWx";

test("patient saves the card with a hidden field and generates a QR", async ({
  page,
}) => {
  let card: Record<string, unknown> = {
    showBloodType: true,
    showAllergies: true,
    showConditions: true,
    showMedications: true,
    showNextOfKin: true,
    showNotes: false,
    bloodType: null,
    allergies: null,
    conditions: null,
    medications: null,
    nextOfKinName: null,
    nextOfKinPhone: null,
    nextOfKinRelation: null,
    notes: null,
    qrToken: null,
    updatedAt: null,
  };
  let saved = null as Record<string, unknown> | null;

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
      return json({
        userId: "p1",
        email: "p@example.com",
        role: "PATIENT",
        emailVerified: true,
      });
    if (path.endsWith("/emergency-card/qr")) {
      card = { ...card, qrToken: req.method() === "POST" ? TOKEN : null };
      return json(card);
    }
    if (path.endsWith("/emergency-card") && req.method() === "PUT") {
      saved = req.postDataJSON() as Record<string, unknown>;
      card = { ...card, ...saved };
      return json(card);
    }
    if (path.endsWith("/emergency-card")) return json(card);
    return json({ items: [], nextCursor: null });
  });

  await page.goto("/en/settings/emergency-card");
  await page.getByLabel("Blood type").fill("O+");
  await page.getByLabel("Allergies").fill("Penicillin");
  await page.getByLabel("Show this field on the emergency card").nth(1).click();
  await page.getByRole("button", { name: "Save emergency card" }).click();
  await expect.poll(() => saved?.bloodType).toBe("O+");
  expect(saved).toMatchObject({ showAllergies: false });

  await page.getByRole("button", { name: "Generate QR code" }).click();
  await expect(
    page.getByRole("img", { name: "QR code that opens your emergency card" }),
  ).toBeVisible();
});
