import { defineRouting } from "next-intl/routing";

// Full target is four locales (en, hi, ta, ml) per CONTEXT.md.
export const routing = defineRouting({
  locales: ["en", "hi", "ta", "ml"],
  defaultLocale: "en",
});
