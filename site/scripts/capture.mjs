// Replays the Pulse demo story against the live stack and saves screenshots.
// Usage: docker compose up --build -d --wait (fresh volumes), then
//   cd site && node scripts/capture.mjs
// Synthetic seeded data only. Password is the seeded demo password (RUNNING.md).
import { chromium } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const BASE = process.env.BASE_URL ?? "http://localhost";
const OUT = join(dirname(fileURLToPath(import.meta.url)), "../src/assets/screens");
const TMP = join(dirname(fileURLToPath(import.meta.url)), "../.capture-tmp");
mkdirSync(OUT, { recursive: true });
mkdirSync(TMP, { recursive: true });

const PASSWORD = "Pulse@demo1";
const PATIENT_ID = "0c96112a-1653-5403-999c-30ec1ef6dda8";
const EMAIL = {
  patient: "demo.patient.en@example.com",
  staff: "staff000@example.com",
  clinician: "clinician0@example.com",
  admin: "admin0@example.com",
};
const DESKTOP = { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 };
const PHONE = { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true };

const browser = await chromium.launch();

async function ctx(device, dark = false) {
  const c = await browser.newContext({ ...device, baseURL: BASE, colorScheme: dark ? "dark" : "light", locale: "en-IN" });
  await c.addInitScript((d) => {
    try { localStorage.setItem("theme", d ? "dark" : "light"); } catch {}
  }, dark);
  return c;
}

async function settle(page) {
  await page.waitForLoadState("networkidle");
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(900);
}

// tall: grow the viewport (not fullPage, which mis-renders sticky headers) and clip to the content.
async function shot(page, name, tall = false) {
  const vp = page.viewportSize();
  let clip;
  if (tall) {
    await page.setViewportSize({ width: vp.width, height: 1500 });
    await settle(page);
    await page.evaluate(() => window.scrollTo(0, 0));
    const bottom = await page.evaluate(() => Math.max(...[...document.querySelectorAll("main *")].map((e) => e.getBoundingClientRect().bottom)));
    clip = { x: 0, y: 0, width: vp.width, height: Math.min(1500, Math.ceil(bottom + 60)) };
  }
  await settle(page);
  await page.screenshot({ path: join(OUT, `${name}.png`), clip });
  if (tall) await page.setViewportSize(vp);
  console.log("shot", name);
}

async function login(page, role) {
  await page.goto("/en/login");
  await settle(page);
  await page.getByLabel("Email address").fill(EMAIL[role]);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL((u) => !u.pathname.endsWith("/login"));
  await settle(page);
}

async function session(role, device = DESKTOP, dark = false) {
  const c = await ctx(device, dark);
  const page = await c.newPage();
  await login(page, role);
  return { c, page };
}

// Attachment: render a small lab-report sheet to PNG with the browser itself.
async function makeAttachment() {
  const c = await browser.newContext({ viewport: { width: 640, height: 420 } });
  const p = await c.newPage();
  await p.setContent(`<body style="font-family:sans-serif;margin:32px;color:#222">
    <h2 style="margin:0 0 4px">Synthetic Diagnostics Lab</h2><div style="color:#666">Specimen report, synthetic demo data</div>
    <hr><table style="width:100%;font-size:18px;border-collapse:collapse">
    <tr><th align=left>Test</th><th align=left>Result</th><th align=left>Reference</th></tr>
    <tr><td>Glucose, fasting</td><td>142 mg/dL</td><td>70 - 100 mg/dL</td></tr></table>
    <p style="color:#666;margin-top:48px">Not a real patient record.</p></body>`);
  const path = join(TMP, "lab-report.png");
  await p.screenshot({ path });
  await c.close();
  return path;
}

const notes = {};

// ---- A. Public screens ----------------------------------------------------
{
  const c = await ctx(DESKTOP);
  const p = await c.newPage();
  await p.goto("/en"); await shot(p, "home-desktop");
  await p.goto("/en/login"); await shot(p, "login-desktop");
  await c.close();
  const d = await ctx(DESKTOP, true);
  const q = await d.newPage();
  await q.goto("/en"); await shot(q, "home-desktop-dark");
  await d.close();

  const m = await ctx(PHONE);
  const r = await m.newPage();
  await r.goto("/en/register"); await settle(r);
  const email = "site.demo.register@example.com";
  await r.getByLabel("Email address").fill(email);
  await r.getByLabel("Password", { exact: true }).fill("TestPassword123!");
  await shot(r, "register-phone");
  await r.getByRole("button", { name: "Create account" }).click();
  try {
    await r.waitForURL(/verify-pending/, { timeout: 8000 });
  } catch {
    await r.goto(`/en/verify-pending?email=${encodeURIComponent(email)}`);
  }
  await shot(r, "verify-pending-phone");
  await m.close();
}

// ---- B. Staff files a lab report ------------------------------------------
const attachment = await makeAttachment();
let entryId;
const staff = await session("staff");
async function fileLab(p, { date, value, attach, name = null }) {
  await p.goto(`/en/patients/${PATIENT_ID}/records`); await settle(p);
  await p.getByRole("link", { name: "File new entry" }).click(); await settle(p);
  await p.getByRole("combobox", { name: "Entry type" }).click();
  await p.getByRole("option", { name: "Lab report" }).click();
  await p.locator('input[type="datetime-local"]').fill(date);
  await p.getByLabel("Code system").fill("LOINC");
  await p.getByLabel("Code", { exact: true }).fill("2345-7");
  await p.getByLabel("Display name").fill("Glucose, fasting");
  await p.getByLabel("Result (numeric)").fill(String(value));
  await p.getByLabel("Unit").fill("mg/dL");
  await p.getByLabel("Reference range — low").fill("70");
  await p.getByLabel("Reference range — high").fill("100");
  if (attach) await p.locator('input[type="file"]').setInputFiles(attach);
  if (name) await shot(p, name, true);
  await p.getByRole("button", { name: "File entry" }).click();
  await p.getByText("View entry").waitFor();
  if (attach) await p.getByText("Document attached.").waitFor({ timeout: 20000 }).catch(() => {});
  const href = await p.getByRole("link", { name: "View entry" }).getAttribute("href");
  return href.split("/").pop();
}
{
  // two earlier results so the analytics lab trend has a line, not one dot
  await fileLab(staff.page, { date: "2026-04-12T09:00", value: 131 });
  await fileLab(staff.page, { date: "2026-07-18T09:00", value: 126 });
  entryId = await fileLab(staff.page, { date: "2026-10-10T09:30", value: 142, attach: attachment, name: "staff-new-entry-desktop" });
  console.log("entry", entryId);
}

// ---- C. Patient: timeline, detail, analytics, profile ---------------------
const patD = await session("patient");
const patM = await session("patient", PHONE);
{
  const p = patM.page;
  await p.goto("/en/timeline"); await shot(p, "timeline-phone");
  await p.goto(`/en/timeline/${entryId}`); await shot(p, "entry-detail-phone");
  await p.goto("/en/profile"); await shot(p, "profile-phone");
  for (const [loc, nm] of [["hi", "timeline-hi-phone"], ["ta", "timeline-ta-phone"], ["ml", "timeline-ml-phone"]]) {
    await p.goto(`/${loc}/timeline`); await shot(p, nm);
  }
}
{
  const p = patD.page;
  await p.goto("/en/timeline"); await shot(p, "timeline-desktop");
  await p.getByRole("combobox", { name: "Filter by type" }).click();
  await p.getByRole("option", { name: "Lab report" }).click();
  await shot(p, "timeline-filters-desktop");
  await p.goto("/en/analytics"); await settle(p);
  await p.getByText("Recent lab trend").first().evaluate((el) => el.scrollIntoView({ block: "start" }));
  await p.evaluate(() => window.scrollBy(0, -110));
  await shot(p, "analytics-desktop");
}

// ---- D. Patient grants consent --------------------------------------------
{
  const p = patD.page;
  await p.goto("/en/consent/new"); await settle(p);
  await p.getByLabel("Clinician email").fill(EMAIL.clinician);
  await p.getByRole("combobox", { name: "Purpose" }).click();
  await p.getByRole("option", { name: "Treatment" }).click();
  await p.locator('input[type="datetime-local"]').fill(new Date(Date.now() + 7 * 864e5).toISOString().slice(0, 16));
  await p.getByRole("radio", { name: "All entry types", exact: true }).check();
  await shot(p, "consent-new-desktop", true);
  await p.getByRole("button", { name: "Review access", exact: true }).click();
  await p.getByRole("heading", { name: "Review before sharing" }).waitFor();
  await p.getByLabel("Confirm with your password").fill(PASSWORD);
  await shot(p, "consent-stepup-desktop");
  await p.getByRole("button", { name: "Grant access" }).click();
  await p.getByText("Access granted").waitFor();
  await patM.page.goto("/en/consent"); await shot(patM.page, "consent-list-phone");
}

// ---- E. Clinician reads, patient revokes, clinician denied + break-glass ---
const clin = await session("clinician");
{
  const p = clin.page;
  await p.goto("/en/clinician"); await p.getByText("Patients who have given you access").waitFor();
  await shot(p, "clinician-home-desktop");
  await p.getByRole("link", { name: PATIENT_ID }).first().click(); await settle(p);
  await p.getByRole("heading", { name: "Patient record" }).waitFor();
  await shot(p, "clinician-records-desktop");
}
{
  const p = patD.page;
  await p.goto("/en/consent"); await settle(p);
  for (let i = 0; i < 3; i++) {
    const row = p.locator("li", { hasText: EMAIL.clinician }).filter({ has: p.getByRole("button", { name: "Revoke" }) });
    if ((await row.count()) === 0) break;
    await row.first().getByRole("button", { name: "Revoke" }).click();
    await row.first().getByRole("button", { name: "Confirm revoke" }).click();
    await p.getByText("Consent revoked. Check remaining current access below.").waitFor();
  }
}
{
  const p = clin.page;
  await p.reload(); await settle(p);
  await p.getByText("Record not found").waitFor();
  await p.getByLabel("Justification").fill("Patient unconscious in the emergency department; consent cannot be obtained.");
  await shot(p, "clinician-denied-desktop", true);
  await p.getByRole("button", { name: "Request emergency access" }).click();
  await settle(p);
}

// ---- F. Patient sees banner, notifications, audit --------------------------
{
  const p = patM.page;
  await p.goto("/en/timeline"); await settle(p);
  await shot(p, "breakglass-banner-phone");
  await p.goto("/en/notifications"); await shot(p, "notifications-phone");
  notes.notifications = await p.locator("main").innerText();
  const d = patD.page;
  await d.goto("/en/audit"); await shot(d, "audit-desktop");
  notes.audit = await d.locator("main").innerText();
}

// ---- G. Staff correction ---------------------------------------------------
{
  const p = staff.page;
  await p.goto(`/en/patients/${PATIENT_ID}/records/${entryId}`); await settle(p);
  await p.getByRole("link", { name: "Correct this entry" }).waitFor();
  await shot(p, "staff-entry-correction-desktop", true);
  await p.getByRole("link", { name: "Correct this entry" }).click(); await settle(p);
  await p.getByLabel("Result (numeric)").fill("118");
  await p.getByRole("button", { name: "File correction" }).click();
  await p.getByText("Correction filed", { exact: true }).waitFor();
  await patM.page.goto(`/en/timeline/${entryId}`); await shot(patM.page, "superseded-entry-phone");
}

// ---- H. Dark timeline ------------------------------------------------------
{
  const s = await session("patient", DESKTOP, true);
  await s.page.goto("/en/timeline"); await shot(s.page, "timeline-desktop-dark");
  await s.c.close();
}

// ---- I. Admin --------------------------------------------------------------
{
  const s = await session("admin");
  const p = s.page;
  await p.goto("/en/admin"); await shot(p, "admin-desktop");
  await p.goto("/en/admin/duplicates"); await settle(p);
  notes.duplicates = await p.locator("main").innerText();
  await shot(p, "admin-duplicates-desktop", true);
  await s.c.close();
}

writeFileSync(join(TMP, "notes.json"), JSON.stringify(notes, null, 2));
await browser.close();
console.log("done");
