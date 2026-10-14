// Repo-relative markdown path <-> guide route. Shared by the content loader
// and the remark link rewriter so the two can never disagree.

export const REPO_URL = "https://github.com/moneytosms/Pulse";

/** Markdown files rendered under /guide. Everything else links to GitHub. */
export const GUIDE_PATTERNS = [
  "docs/**/*.md",
  "!docs/archive/**",
  "!docs/superpowers/**",
  "CONTEXT.md",
  "README.md",
  "RUNNING.md",
  "DESIGN.md",
  "seed/README.md",
];

const SPECIAL = {
  "docs/README.md": "index",
  "README.md": "readme",
  "seed/README.md": "seed",
};

/** "docs/adr/0001-x.md" -> "adr/0001-x"; "docs/workflows/README.md" -> "workflows". */
export function slugFor(repoPath) {
  if (SPECIAL[repoPath]) return SPECIAL[repoPath];
  return repoPath
    .replace(/\.md$/, "")
    .replace(/^docs\//, "")
    .replace(/\/README$/, "")
    .toLowerCase();
}

/** Mirrors GUIDE_PATTERNS for a single path. */
export function isGuidePath(repoPath) {
  if (!repoPath.endsWith(".md")) return false;
  if (SPECIAL[repoPath] || ["CONTEXT.md", "RUNNING.md", "DESIGN.md"].includes(repoPath)) return true;
  return (
    repoPath.startsWith("docs/") &&
    !repoPath.startsWith("docs/archive/") &&
    !repoPath.startsWith("docs/superpowers/")
  );
}
