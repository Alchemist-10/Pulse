import { expect, test } from "@playwright/test";

// Every backend call is mocked here — no FastAPI / Postgres / Redis needed.
const FIXTURE_PROFILE = {
  id: "11111111-1111-1111-1111-111111111111",
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

test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    const json = (status: number, body: unknown) =>
      route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(body),
      });

    if (url.includes("/auth/register")) return json(201, { userId: "u1" });
    if (url.includes("/auth/login")) return json(200, { userId: "u1", role: "PATIENT" });
    if (url.includes("/patients/me")) return json(200, FIXTURE_PROFILE);
    return json(404, { error: { code: "NOT_FOUND", message: "not found" } });
  });
});

test("register form shows validation errors on bad input", async ({ page }) => {
  await page.goto("/en/register");
  // Submit empty: three field errors appear from client-side validation.
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText("Enter your email address.")).toBeVisible();
  await expect(page.getByText("Enter a password.")).toBeVisible();
  await expect(page.getByText("Choose a role.")).toBeVisible();

  // A too-short password is rejected without a network call.
  await page.getByLabel("Email address").fill("not-an-email");
  await page.getByLabel("Password").fill("short");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText("Enter a valid email address.")).toBeVisible();
  await expect(page.getByText("Use at least 12 characters.")).toBeVisible();
});

test("EN <-> HI toggle changes the URL locale prefix and a visible string", async ({
  page,
}) => {
  await page.goto("/en/login");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();

  await page.getByRole("button", { name: "हिन्दी" }).click();

  await expect(page).toHaveURL(/\/hi\/login$/);
  await expect(page.getByRole("heading", { name: "साइन इन करें" })).toBeVisible();
});

test("locale switcher lists all four locales", async ({ page }) => {
  await page.goto("/en/login");
  const group = page.getByRole("group", { name: "Language" });
  await expect(group.getByRole("button", { name: "English" })).toBeVisible();
  await expect(group.getByRole("button", { name: "हिन्दी" })).toBeVisible();
  await expect(group.getByRole("button", { name: "தமிழ்" })).toBeVisible();
  await expect(group.getByRole("button", { name: "മലയാളം" })).toBeVisible();
});

// ta/ml catalogs ship with every key present and every value empty (P2.10) —
// real translations land in Phase 4. next-intl only raises MISSING_MESSAGE for
// an absent key, so request.ts prunes empty leaves first; the guard then fires
// in dev and CI. This is the test that keeps an untranslated locale a red build
// instead of a page of silent blanks.
test("ta locale throws on an untranslated key in dev", async ({ page }) => {
  const response = await page.goto("/ta/login");
  expect(response?.status()).toBe(500);
});

test("/api/* is not rewritten by the locale middleware", async ({ page }) => {
  // The matcher (src/middleware.ts) excludes /api so Caddy's FastAPI route is
  // untouched. Hitting an unmocked /api path directly (no page.route stub for
  // this specific one) must reach Next's own 404 handler at the literal path —
  // if the middleware ever rewrote it to /en/api/... it would 404 differently
  // or redirect, which this assertion would catch.
  const response = await page.goto("/api/v1/does-not-exist");
  expect(response?.status()).toBe(404);
  expect(page.url()).toContain("/api/v1/does-not-exist");
});

test("login redirects to the profile and renders identity fields", async ({ page }) => {
  await page.goto("/en/login");
  await page.getByLabel("Email address").fill("aarav@example.com");
  await page.getByLabel("Password").fill("correct horse battery");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/en\/profile$/);
  await expect(page.getByRole("heading", { name: "Your profile" })).toBeVisible();
  await expect(page.getByText("Aarav Menon")).toBeVisible();
  // Date rendered day-first via Intl (en-IN), not the raw ISO string.
  await expect(page.getByText("12 Apr 1990")).toBeVisible();
});
