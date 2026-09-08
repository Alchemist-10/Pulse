import { defineConfig, devices } from "@playwright/test";

// Smoke only. The dev server is the whole backend the smoke needs — every
// `/api/v1/*` call is mocked inside the specs via page.route, so the suite is
// self-contained and needs no FastAPI, Postgres, or Redis.
//
// `next build` is not used here — the upstream Turbopack prerender crash
// (docs/tech-stack.md) means the verification path is `next dev` + tsc + lint.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
