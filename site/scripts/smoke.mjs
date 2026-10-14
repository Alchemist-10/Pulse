// Run against `npm run build` + `npm run preview`, including the Pages base path.
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { chromium } from "playwright";

const url = process.env.SITE_URL ?? "http://127.0.0.1:4321/Pulse/";
const output = path.resolve(process.env.QA_OUTPUT_DIR ?? "test-results/site");
await mkdir(output, { recursive: true });
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
  ?? (existsSync("/usr/bin/chromium") ? "/usr/bin/chromium" : undefined);
const browser = await chromium.launch({ executablePath, headless: true });
const report = [];
const chapters = ["problem", "promise", "people", "record-life", "sharing", "consent-engine", "audit",
  "data-model", "analytics", "duplicates", "seed", "architecture", "patterns", "stack", "locales",
  "decisions", "proof", "different", "built", "faq", "run"];

async function checkOverflow(page, label) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
  assert.equal(overflow, false, `${label}: horizontal overflow`);
}

try {
  for (const width of [375, 768, 1440]) {
    for (const colorScheme of ["light", "dark"]) {
      const label = `${width}-${colorScheme}`;
      const context = await browser.newContext({ viewport: { width, height: 900 }, colorScheme });
      const page = await context.newPage();
      const errors = [];
      page.on("pageerror", (e) => errors.push(e.message));
      const response = await page.goto(url);
      assert.equal(response.status(), 200);
      await page.evaluate(() => document.fonts.ready);
      await page.waitForTimeout(1600);
      assert.equal(await page.locator(".chapter").count(), chapters.length);
      assert.equal(await page.getByText("Screenshot pending", { exact: false }).count(), 0);
      for (const id of chapters) {
        await page.locator(`#${id}`).scrollIntoViewIfNeeded();
        await page.waitForTimeout(80);
        await checkOverflow(page, `${label}/${id}`);
      }
      await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
      await page.waitForTimeout(300);
      await page.screenshot({ path: path.join(output, `${label}.png`), fullPage: true });
      const geometry = await page.evaluate(() => Object.fromEntries(
        [...document.querySelectorAll(".chapter")].map((chapter) => {
          const head = chapter.querySelector(".chapter__head").getBoundingClientRect();
          const body = chapter.querySelector(".chapter__body").getBoundingClientRect();
          return [chapter.id, { head: head.top + scrollY, body: body.top + scrollY }];
        }),
      ));
      await writeFile(path.join(output, `${label}-geometry.json`), JSON.stringify(geometry));

      // These exercise mechanisms, rather than duplicating implementation details.
      await page.locator('[data-pick="ADMINISTRATOR"]').click();
      await page.locator('[data-panel="ADMINISTRATOR"]').waitFor({ state: "visible" });
      await page.locator("[data-life-toggle]").click();
      assert.equal(await page.locator("[data-life-toggle]").getAttribute("aria-pressed"), "true");
      await page.locator('[data-share-step="2"]').click();
      assert.match(await page.locator("[data-share-state]").innerText(), /Permission removed/);
      await page.locator("[data-pair]").last().click();
      assert.match(await page.locator("[data-decision]").innerText(), /Below review threshold/);
      await page.locator('[data-locale-button="ml"]').click();
      await page.locator('[data-locale-panel="ml"]').waitFor({ state: "visible" });
      assert.equal(await page.locator(".locale__clinical strong").innerText(), "Type 2 diabetes mellitus");
      await page.locator("#consent-engine .codeblock summary").click();
      assert.equal(await page.locator("#consent-engine .codeblock pre").isVisible(), true);
      await page.locator('input[name="consent"][value="revoked"]').check();
      await page.locator("[data-send]").click();
      await page.waitForFunction(() => document.querySelector("[data-status]")?.textContent?.includes("HTTP 404"));
      assert.match(await page.locator("[data-audit] li").first().innerText(), /ACCESS_DENIED/);
      await page.locator('input[name="consent"][value="active"]').check();
      await page.locator("[data-send]").click();
      await page.waitForFunction(() => document.querySelector("[data-status]")?.textContent?.includes("HTTP 200"));
      await page.locator("[data-replay]").click();
      await page.waitForFunction(() => document.querySelector("[data-proof-pipeline]")?.classList.contains("is-run"));
      await page.locator("#faq details").last().locator("summary").click();
      assert.equal(await page.locator("#faq details").last().getAttribute("open"), "");

      await page.goto(new URL("guide/", url).href);
      await page.locator(".pagefind-ui__search-input").fill("revocation");
      await page.locator(".pagefind-ui__result-link").first().waitFor({ state: "visible" });
      const href = await page.locator(".pagefind-ui__result-link").first().getAttribute("href");
      assert.ok(new URL(href, page.url()).pathname.startsWith("/Pulse/guide/"), `search loses base: ${href}`);
      await checkOverflow(page, `${label}/guide`);
      await page.screenshot({ path: path.join(output, `guide-${label}.png`) });
      assert.deepEqual(errors, [], `${label}: browser exceptions`);
      report.push({ viewport: width, theme: colorScheme, chapters: chapters.length, consoleErrors: errors.length });
      await context.close();
    }
  }

  for (const mode of ["no-js", "reduced-motion"]) {
    const context = await browser.newContext({ viewport: { width: 375, height: 812 },
      javaScriptEnabled: mode !== "no-js", reducedMotion: "reduce" });
    const page = await context.newPage();
    await page.goto(url);
    assert.equal(await page.locator(".chapter").count(), chapters.length);
    await checkOverflow(page, mode);
    if (mode === "no-js") {
      for (const role of ["PATIENT", "PROVIDER_STAFF", "CLINICIAN", "ADMINISTRATOR"]) {
        assert.equal(await page.locator(`[data-panel="${role}"]`).isVisible(), true);
      }
      for (const locale of ["en", "hi", "ta", "ml"]) {
        assert.equal(await page.locator(`[data-locale-panel="${locale}"]`).isVisible(), true);
      }
      await page.locator("#consent-engine .codeblock summary").click();
      assert.equal(await page.locator("#consent-engine .codeblock pre").isVisible(), true);
    } else {
      await page.locator('input[name="consent"][value="expired"]').check();
      await page.locator("[data-send]").click();
      assert.match(await page.locator("[data-status]").innerText(), /HTTP 404/);
    }
    await page.screenshot({ path: path.join(output, `${mode}.png`) });
    report.push({ mode, chapters: chapters.length });
    await context.close();
  }
  await writeFile(path.join(output, "report.json"), JSON.stringify(report, null, 2));
  console.log(`Site smoke passed: ${report.length} modes, ${chapters.length} chapters, guide search and consent verified.`);
} finally {
  await browser.close();
}
