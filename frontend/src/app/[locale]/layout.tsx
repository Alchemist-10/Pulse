import type { Metadata } from "next";
import type { ReactNode } from "react";
import { hasLocale, NextIntlClientProvider, useTranslations } from "next-intl";
import { notFound } from "next/navigation";
import { ActivityIcon } from "@/components/ui/icons";
import { LocaleSwitcher } from "@/components/LocaleSwitcher";
import { Link } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";
import "../globals.css";
import "../fonts";

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export const metadata: Metadata = {
  title: "Pulse",
};

type Props = {
  children: ReactNode;
  params: Promise<{ locale: string }>;
};

// Sync Server Component so next-intl's `useTranslations` is available for the
// chrome (header, skip link, footer).
function Shell({ children }: { children: ReactNode }) {
  const t = useTranslations("app");
  return (
    <>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:m-2 focus:rounded focus:bg-accent focus:px-3 focus:py-2 focus:text-accent-contrast"
      >
        {t("skipToContent")}
      </a>
      <div className="flex min-h-dvh flex-col">
        <header className="sticky top-0 z-40 border-b border-border bg-surface/85 backdrop-blur supports-[backdrop-filter]:bg-surface/70">
          <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
            <Link
              href="/"
              className="flex items-center gap-2 rounded-md text-base font-bold tracking-tight text-foreground outline-none focus-visible:ring-2 focus-visible:ring-focus-ring"
            >
              <span className="flex size-7 items-center justify-center rounded-lg bg-gradient-accent text-accent-contrast">
                <ActivityIcon className="size-4" strokeWidth={2.5} />
              </span>
              {t("name")}
            </Link>
            <LocaleSwitcher />
          </div>
        </header>
        <main id="main" className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:py-10">
          {children}
        </main>
        <footer className="border-t border-border">
          <div className="mx-auto flex max-w-5xl flex-col gap-1 px-4 py-5 text-xs text-muted sm:flex-row sm:items-center sm:justify-between">
            <p>
              {t("name")} — {t("tagline")}
            </p>
            <p>{t("confidentialityNote")}</p>
          </div>
        </footer>
      </div>
    </>
  );
}

export default async function LocaleLayout({ children, params }: Props) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  return (
    <html lang={locale}>
      <body className="min-h-dvh">
        <NextIntlClientProvider>
          <Shell>{children}</Shell>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
