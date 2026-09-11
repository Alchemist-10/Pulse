"use client";

import { useTranslations } from "next-intl";
import { ApiError } from "./api";

/**
 * Resolve an error to a localized, user-facing string.
 *
 * We render from `error.code` against the `errors` catalog namespace and never
 * from `error.message` (ADR-0013) — the backend message is English-only and
 * unstable, the code is stable forever. An unrecognized code falls back to the
 * generic string so a new backend code never renders as a blank or a raw token.
 */
export function useApiErrorMessage(): (error: unknown) => string {
  const t = useTranslations("errors");

  return (error: unknown): string => {
    if (error instanceof ApiError && t.has(error.code)) {
      return t(error.code);
    }
    return t("GENERIC");
  };
}

/**
 * Field-level error codes from a 422's `details` array (docs/api-conventions.md:
 * `[{ field, code }]`, `field` dotted from the request root e.g. "body.entryType").
 * Keyed by form field name — the leading "body." is stripped, and the wire is
 * already camelCase (PulseSchema alias generator), so the key matches the
 * input's own name with no further conversion.
 */
export function fieldCodesFrom(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError) || !error.details) return {};
  const out: Record<string, string> = {};
  for (const { field, code } of error.details) {
    if (!field || !code) continue;
    out[field.startsWith("body.") ? field.slice(5) : field] = code;
  }
  return out;
}

/**
 * Field-level errors from a 422, keyed by form field name, translated to a
 * user-facing string — an unrecognized validation code falls back to a
 * generic per-field message rather than rendering a raw code.
 */
export function useFieldErrors(): (error: unknown) => Record<string, string> {
  const t = useTranslations("errors");

  return (error: unknown): Record<string, string> => {
    const codes = fieldCodesFrom(error);
    const out: Record<string, string> = {};
    for (const [field, code] of Object.entries(codes)) {
      const key = `fieldErrors.${code}`;
      out[field] = t.has(key) ? t(key) : t("fieldErrors.GENERIC");
    }
    return out;
  };
}
