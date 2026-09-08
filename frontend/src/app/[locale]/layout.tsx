import type { Metadata } from "next";
import type { ReactNode } from "react";
import { hasLocale, NextIntlClientProvider, useTranslations } from "next-intl";
import { notFound } from "next/navigation";
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
// chrome (header, skip link).
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
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
          <Link href="/" className="text-base font-bold text-foreground">
            {t("name")}
          </Link>
          <LocaleSwitcher />
        </div>
      </header>
      <main id="main" className="mx-auto max-w-3xl px-4 py-8">
        {children}
      </main>
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
