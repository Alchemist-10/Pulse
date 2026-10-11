import { expect, test, type Page, type Route } from "@playwright/test";

const json = (route: Route, body: unknown, status = 200) =>
  route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
const notification = {
  id: "recent-notification",
  type: "CONSENT_REVOKED",
  title: "LEGACY_ENGLISH",
  body: "LEGACY_ENGLISH",
  params: {},
  readAt: null as string | null,
  createdAt: "2026-10-11T06:00:00Z",
};

async function base(page: Page, role = "PATIENT") {
  await page.route("**/api/v1/**", (route) => {
    if (new URL(route.request().url()).pathname.endsWith("/auth/me"))
      return json(route, {
        userId: "patient",
        role,
        email: "patient@example.com",
        emailVerified: true,
      });
    return json(route, { items: [], nextCursor: null });
  });
}
const bell = (page: Page) =>
  page.getByRole("button", {
    name: /^Notifications(?:, unread recent activity)?$/,
  });

test("bell refreshes recent messages, preserves unread state, and supports keyboard dismissal", async ({
  page,
}) => {
  await base(page);
  let latest = false;
  let writes = 0;
  await page.route("**/api/v1/notifications?*", (route) => {
    if (route.request().method() !== "GET") writes++;
    expect(new URL(route.request().url()).searchParams.get("limit")).toBe("5");
    return json(route, {
      items: latest ? [notification] : [],
      nextCursor: null,
    });
  });
  await page.goto("/en/consent");
  await bell(page).click();
  await expect(
    page
      .getByRole("dialog", { name: "Notifications", exact: true })
      .getByText("No notifications yet"),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(bell(page)).toBeFocused();
  latest = true;
  await page.keyboard.press("Enter");
  const panel = page.getByRole("dialog", {
    name: "Notifications",
    exact: true,
  });
  await expect(
    panel.getByText("Consent revoked", { exact: true }),
  ).toBeVisible();
  await expect(panel.getByText("Unread", { exact: true })).toBeVisible();
  await expect(panel.getByText("LEGACY_ENGLISH")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Notifications, unread recent activity" }),
  ).toBeVisible();
  expect(writes).toBe(0);
  await panel.getByRole("button", { name: "Close notifications" }).click();
  await expect(bell(page)).toBeFocused();
});

test("preview offers retry after failure and announces loading instead of an empty inbox", async ({
  page,
}) => {
  await base(page);
  let fail = true;
  await page.route("**/api/v1/notifications?*", (route) =>
    fail
      ? json(
          route,
          { error: { code: "GENERIC", message: "Do not display server text" } },
          500,
        )
      : json(route, { items: [], nextCursor: null }),
  );
  await page.goto("/en/consent");
  await bell(page).click();
  const panel = page.getByRole("dialog", {
    name: "Notifications",
    exact: true,
  });
  await expect(
    panel.getByText("Could not load your notifications"),
  ).toBeVisible();
  await expect(panel.getByText("No notifications yet")).toHaveCount(0);
  await expect(panel.getByText("Do not display server text")).toHaveCount(0);
  fail = false;
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/v1/notifications?*", async (route) => {
    await gate;
    await json(route, { items: [], nextCursor: null });
  });
  await panel.getByRole("button", { name: "Try again" }).click();
  await expect(panel.getByText("Loading your notifications…")).toBeAttached();
  await expect(panel.getByText("No notifications yet")).toHaveCount(0);
  release();
  await expect(panel.getByText("No notifications yet")).toBeVisible();
});

test("marking a notification read in the full list refreshes the header indicator", async ({
  page,
}) => {
  await base(page);
  let readAt: string | null = null;
  await page.route("**/api/v1/notifications?*", (route) =>
    json(route, {
      items: [{ ...notification, readAt }],
      nextCursor: null,
    }),
  );
  await page.route(
    "**/api/v1/notifications/recent-notification/read",
    (route) => {
      expect(route.request().method()).toBe("POST");
      readAt = "2026-10-11T07:00:00Z";
      return json(route, { ...notification, readAt });
    },
  );
  await page.goto("/en/consent");
  await expect(
    page.getByRole("button", { name: "Notifications, unread recent activity" }),
  ).toBeVisible();
  await bell(page).click();
  await page.getByRole("link", { name: "View all notifications" }).click();
  await expect(page).toHaveURL(/\/en\/notifications$/);
  await page.getByRole("button", { name: "Mark as read", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Notifications", exact: true }),
  ).toBeVisible();
  await bell(page).click();
  await expect(
    page
      .getByRole("dialog", { name: "Notifications", exact: true })
      .getByText("Read", { exact: true }),
  ).toBeVisible();
});

test("notification preview fits all four locales on mobile and a translated desktop header", async ({
  page,
}) => {
  await base(page);
  await page.route("**/api/v1/notifications?*", (route) =>
    json(route, { items: [notification], nextCursor: null }),
  );
  const labels = {
    en: "Notifications",
    hi: "सूचनाएं",
    ta: "அறிவிப்புகள்",
    ml: "അറിയിപ്പുകൾ",
  };
  for (const width of [360, 1280]) {
    await page.setViewportSize({ width, height: 844 });
    for (const [locale, title] of Object.entries(labels)) {
      await page.goto(`/${locale}/consent`);
      await page.getByRole("button", { name: new RegExp(`^${title}`) }).click();
      const panel = page.getByRole("dialog", { name: title, exact: true });
      await expect(panel.locator("li")).toHaveCount(1);
      const box = await panel.boundingBox();
      expect(box).not.toBeNull();
      expect(box!.x).toBeGreaterThanOrEqual(0);
      expect(box!.x + box!.width).toBeLessThanOrEqual(width);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      expect(
        await panel.evaluate(
          (element) => element.scrollWidth <= element.clientWidth,
        ),
      ).toBe(true);
      await page.keyboard.press("Escape");
    }
  }
});

test("bell is absent for staff and after logout, and ignores cancelled old messages", async ({
  page,
}) => {
  await base(page, "CLINICIAN");
  let notificationReads = 0;
  await page.route("**/api/v1/notifications?*", (route) => {
    notificationReads++;
    return json(route, { items: [notification], nextCursor: null });
  });
  await page.goto("/en/clinician");
  await expect(
    page.getByRole("button", { name: "Account", exact: true }),
  ).toBeVisible();
  await expect(bell(page)).toHaveCount(0);
  expect(notificationReads).toBe(0);

  await base(page);
  let signedOut = false;
  await page.route("**/api/v1/auth/me", (route) =>
    signedOut
      ? json(
          route,
          { error: { code: "SESSION_EXPIRED", message: "Expired" } },
          401,
        )
      : json(route, {
          userId: "patient",
          role: "PATIENT",
          email: "patient@example.com",
          emailVerified: true,
        }),
  );
  await page.route("**/api/v1/auth/logout", (route) => {
    signedOut = true;
    return route.fulfill({ status: 204 });
  });
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/v1/notifications?*", async (route) => {
    await gate;
    await json(route, { items: [notification], nextCursor: null }).catch(
      () => {},
    );
  });
  await page.goto("/en/consent");
  await expect(bell(page)).toBeVisible();
  await page.getByRole("button", { name: "Account", exact: true }).click();
  await page.getByRole("menuitem", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/en\/login$/);
  release();
  await expect(bell(page)).toHaveCount(0);
  await expect(page.getByText("Consent revoked", { exact: true })).toHaveCount(
    0,
  );
});
