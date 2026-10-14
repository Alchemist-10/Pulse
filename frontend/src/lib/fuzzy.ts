// Small typo-tolerant matcher for short lists already on screen (names).
// Not a server search: results never leave the data the user may read.
const norm = (s: string) =>
  s
    .normalize("NFKD")
    .replace(/\p{M}/gu, "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();

function trigrams(s: string): Set<string> {
  const padded = `  ${s} `;
  const out = new Set<string>();
  for (let i = 0; i < padded.length - 2; i++) out.add(padded.slice(i, i + 3));
  return out;
}

/** 0..1; 1 when `query` is a substring or token-prefix of `text`. */
export function fuzzyScore(query: string, text: string): number {
  const q = norm(query);
  const t = norm(text);
  if (!q) return 1;
  if (t.includes(q)) return 1;
  const tokens = t.split(" ");
  const parts = q.split(" ");
  if (parts.every((p) => tokens.some((tok) => tok.startsWith(p)))) return 1;
  const a = trigrams(q);
  const b = trigrams(t);
  let shared = 0;
  for (const g of a) if (b.has(g)) shared++;
  return shared / Math.min(a.size, b.size);
}

export function fuzzyFilter<T>(
  items: T[],
  query: string,
  text: (item: T) => string,
  threshold = 0.4,
): T[] {
  if (!query.trim()) return items;
  return items
    .map((item) => ({ item, score: fuzzyScore(query, text(item)) }))
    .filter((r) => r.score >= threshold)
    .sort((x, y) => y.score - x.score)
    .map((r) => r.item);
}
