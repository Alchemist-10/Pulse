"use client";

import { useTranslations } from "next-intl";
import { Link, usePathname } from "@/i18n/navigation";
import { cn } from "@/lib/utils";

const TABS = [
  { key: "profile", href: "/settings/profile" },
  { key: "notifications", href: "/settings/notifications" },
  { key: "emergencyCard", href: "/settings/emergency-card" },
  { key: "scan", href: "/settings/scan" },
] as const;

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const t = useTranslations("settings");
  const pathname = usePathname();
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          {t("title")}
        </h1>
      </div>
      <nav
        aria-label={t("title")}
        className="-mx-1 flex gap-1 overflow-x-auto px-1 pb-1"
      >
        {TABS.map(({ key, href }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={key}
              href={href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "min-h-11 shrink-0 rounded-lg px-4 py-2.5 text-sm font-medium focus-visible:outline-2 focus-visible:outline-ring",
                active
                  ? "bg-primary-soft text-primary"
                  : "text-muted-foreground hover:bg-muted",
              )}
            >
              {t(`tabs.${key}`)}
            </Link>
          );
        })}
      </nav>
      {children}
    </div>
  );
}
