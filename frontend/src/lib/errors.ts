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

/** Field-level errors from a 422, keyed by form field name. */
export function fieldErrorsFrom(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError) || !error.details) return {};
  const out: Record<string, string> = {};
  for (const [field, value] of Object.entries(error.details)) {
    if (typeof value === "string") out[field] = value;
    else if (Array.isArray(value) && typeof value[0] === "string") out[field] = value[0];
  }
  return out;
}
