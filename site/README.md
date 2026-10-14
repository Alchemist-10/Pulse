# Pulse story and guide

The static Astro + GSAP site publishes at [moneytosms.github.io/Pulse](https://moneytosms.github.io/Pulse/). It presents the implemented project to a software architecture grader, then renders the repository's own documents as a searchable guide. The Pulse application remains in `frontend/` and `backend/`.

## Develop and verify

Use Node 24 or newer. From this directory:

```bash
npm ci
npm run dev
```

For the production output, including Pagefind search:

```bash
npm run check
npm run build
npm run verify
npx playwright install chromium
npm run preview -- --background --host 127.0.0.1 --port 4321
npm test
npx astro preview stop
```

The preview URL is `http://127.0.0.1:4321/Pulse/`. `SITE_URL` can point the smoke check at another deployment. `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` can select a system browser. The smoke check covers 375, 768 and 1440 px, both themes, consent outcomes, role selection, guide search, reduced motion and JavaScript disabled; its report and captures go to ignored `test-results/site/` (or `QA_OUTPUT_DIR`). The static verifier checks local links, image variants, anchors, Markdown links and screenshot placeholders.

## Keep claims grounded

Shared counts and boundaries live in [`src/data/facts.ts`](src/data/facts.ts). Chapter-specific evidence lives in `story-*.ts`. Recheck those sources when the application changes. Literal code samples use the build-time `sourceExcerpt` helper. The guide reads Markdown directly from the repository and rewrites its links; there are no second copies of the documents to maintain.

The visual authority is [`../DESIGN.md`](../DESIGN.md) and the application theme in `frontend/src/app/globals.css`. The site's ECG spine follows the chapter sequence. Motion enhances readable static content and respects reduced motion. See [`CONTRIBUTING-SECTIONS.md`](CONTRIBUTING-SECTIONS.md) for the chapter contract.

## Screenshots and publishing

The 29 images in `src/assets/screens/` are genuine captures of seeded synthetic data, recorded by [`scripts/capture.mjs`](scripts/capture.mjs). The capture script creates entries and exercises consent, correction and emergency access, so use a disposable fresh demo stack. Never run it against real patient data or a database you need to preserve. See the repository [running guide](../RUNNING.md) for demo setup.

The [Pages workflow](../.github/workflows/pages.yml) checks and publishes pushes to `main`; pull requests run its checks without publishing. Team and course credits intentionally remain placeholders in `facts.ts`, awaiting confirmation. There is no demo video to embed.
