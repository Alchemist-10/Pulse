// @ts-check
import { defineConfig } from "astro/config";
import { unified } from "@astrojs/markdown-remark";
import { rewriteRepoLinks } from "./src/lib/remark-repo-links.mjs";

// GitHub Pages project site: https://moneytosms.github.io/Pulse/
export default defineConfig({
  site: "https://moneytosms.github.io",
  base: "/Pulse",
  trailingSlash: "ignore",
  // Preserve spaces around inline expressions and links under Astro 7.
  compressHTML: true,
  markdown: {
    processor: unified({ remarkPlugins: [rewriteRepoLinks] }),
    shikiConfig: {
      themes: { light: "github-light", dark: "github-dark-dimmed" },
      defaultColor: false,
    },
  },
});
