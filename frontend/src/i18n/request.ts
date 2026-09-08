import { hasLocale } from "next-intl";
import { getRequestConfig } from "next-intl/server";
import { routing } from "./routing";

// One catalog file per feature per locale, so four people editing translations
// do not conflict on every PR (.claude/rules/frontend.md). `common.json` is
// spread at the root (it groups its own keys: `app`, `home`, `locale`, …);
// every other file is mounted under a namespace matching its filename.
//
// Static imports (not a dynamic `import(\`...${ns}\`)`) so the bundler resolves
// every catalog at build time and a missing file is a build error.
import enCommon from "./messages/en/common.json";
import enAuth from "./messages/en/auth.json";
import enErrors from "./messages/en/errors.json";
import enProfile from "./messages/en/profile.json";
import hiCommon from "./messages/hi/common.json";
import hiAuth from "./messages/hi/auth.json";
import hiErrors from "./messages/hi/errors.json";
import hiProfile from "./messages/hi/profile.json";

type Catalog = Record<string, unknown>;

const CATALOGS: Record<string, Catalog> = {
  en: { ...enCommon, auth: enAuth, errors: enErrors, profile: enProfile },
  hi: { ...hiCommon, auth: hiAuth, errors: hiErrors, profile: hiProfile },
};

function mergeCatalogs(base: Catalog, override: Catalog): Catalog {
  const out: Catalog = { ...base };
  for (const [key, value] of Object.entries(override)) {
    out[key] =
      value && typeof value === "object" && !Array.isArray(value)
        ? { ...(base[key] as object), ...(value as object) }
        : value;
  }
  return out;
}

export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale;
  const locale = hasLocale(routing.locales, requested)
    ? requested
    : routing.defaultLocale;

  const isProduction = process.env.NODE_ENV === "production";

  // Dev and CI: use only the requested locale, so a missing key throws.
  // Production: layer the requested locale over an English base so a gap
  // degrades to English rather than crashing a live page.
  const messages =
    isProduction && locale !== routing.defaultLocale
      ? mergeCatalogs(CATALOGS[routing.defaultLocale], CATALOGS[locale])
      : CATALOGS[locale];

  return {
    locale,
    messages,
    onError(error) {
      if (error.code === "MISSING_MESSAGE" && !isProduction) {
        // Fail loud in dev and CI — a missing Hindi string must not reach review.
        throw error;
      }
      console.error(error);
    },
  };
});
