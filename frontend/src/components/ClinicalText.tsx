import type { ReactNode } from "react";

/**
 * Renders clinical content verbatim, in every locale.
 *
 * Medication names, test names, diagnoses and note text are recorded facts, not
 * interface copy — translating "Type 2 diabetes mellitus" would be inventing a
 * medical claim (CONTEXT.md, .claude/rules/clinical-safety.md). No clinical
 * string ever passes through next-intl; it comes from the API and renders as-is.
 *
 * `translate="no"` also tells browser/extension auto-translation to leave it
 * alone. Phase 1 has no clinical data yet — this exists so the first clinical
 * string added has a correct path and cannot be wired through a catalog.
 */
export function ClinicalText({ children }: { children: ReactNode }) {
  return (
    <span translate="no" className="notranslate">
      {children}
    </span>
  );
}
