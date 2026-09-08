"use client";

import { useTransition } from "react";
import { useLocale, useTranslations } from "next-intl";
import { usePathname, useRouter } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";
import { cn } from "@/lib/cn";

// Each language labelled in its own name, so a reader can always find their
// own regardless of the language the page is currently in.
const AUTONYMS: Record<string, string> = {
  en: "English",
  hi: "हिन्दी",
};

// EN <-> HI. Preserves the current path (next-intl navigation strips and
// re-adds the locale prefix) and the query string.
export function LocaleSwitcher() {
  const t = useTranslations("locale");
  const activeLocale = useLocale();
  const pathname = usePathname();
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  return (
    <div
      className="inline-flex overflow-hidden rounded-md border border-border-strong"
      role="group"
      aria-label={t("label")}
    >
      {routing.locales.map((locale) => {
        const active = locale === activeLocale;
        return (
          <button
            key={locale}
            type="button"
            lang={locale}
            aria-current={active ? "true" : undefined}
            disabled={active || isPending}
            onClick={() =>
              startTransition(() => {
                router.replace(pathname, { locale });
              })
            }
            className={cn(
              "min-h-9 px-3 py-1 text-sm font-medium transition-colors",
              active
                ? "bg-accent text-accent-contrast"
                : "bg-surface text-accent-text hover:bg-accent-subtle",
            )}
          >
            {AUTONYMS[locale] ?? locale}
          </button>
        );
      })}
    </div>
  );
}
