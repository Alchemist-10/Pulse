"use client";

import { useTranslations } from "next-intl";
import { BackButton } from "@/components/BackButton";
import { Link } from "@/i18n/navigation";
import { cn } from "@/lib/utils";

// Back plus the two views a clinician has of one patient. Both routes are
// consent/break-glass gated server-side; this is navigation only.
export function PatientSubNav({
  patientId,
  active,
  backFallback = "/clinician",
}: {
  patientId: string;
  active: "records" | "emergency";
  backFallback?: string;
}) {
  const t = useTranslations("clinicianRecords.nav");
  const tabs = [
    { key: "records", href: `/patients/${patientId}/records` },
    { key: "emergency", href: `/patients/${patientId}/emergency` },
  ] as const;
  return (
    <div className="space-y-2">
      <BackButton fallback={backFallback} />
      <nav aria-label={t("label")} className="flex gap-1">
        {tabs.map(({ key, href }) => (
          <Link
            key={key}
            href={href}
            aria-current={active === key ? "page" : undefined}
            className={cn(
              "min-h-11 rounded-lg px-4 py-2.5 text-sm font-medium focus-visible:outline-2 focus-visible:outline-ring",
              active === key
                ? "bg-primary-soft text-primary"
                : "text-muted-foreground hover:bg-muted",
            )}
          >
            {t(key)}
          </Link>
        ))}
      </nav>
    </div>
  );
}
