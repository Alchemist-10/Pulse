"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { api } from "@/lib/api";
import type { EntrySummary, Page } from "@/lib/records";

// Newer / older neighbour of one entry within the first page of the same
// timeline the actor is already allowed to read. Silent when not found.
export function EntryPager({
  patientId,
  entryId,
}: {
  patientId: string;
  entryId: string;
}) {
  const t = useTranslations("clinicianRecords.nav");
  const [ids, setIds] = useState<string[] | null>(null);

  useEffect(() => {
    let active = true;
    api
      .get<Page<EntrySummary>>(`/patients/${patientId}/entries?limit=100`)
      .then((page) => active && setIds(page.items.map((e) => e.id)))
      .catch(() => active && setIds(null));
    return () => {
      active = false;
    };
  }, [patientId]);

  const index = ids ? ids.indexOf(entryId) : -1;
  if (!ids || index < 0) return null;
  const newer = index > 0 ? ids[index - 1] : null;
  const older = index < ids.length - 1 ? ids[index + 1] : null;
  const href = (id: string) => `/patients/${patientId}/records/${id}` as const;
  return (
    <nav
      aria-label={t("pager")}
      className="flex items-center justify-between gap-2"
    >
      {newer ? (
        <Button asChild variant="outline" size="sm">
          <Link href={href(newer)}>
            <ChevronLeftIcon />
            {t("newer")}
          </Link>
        </Button>
      ) : (
        <span />
      )}
      <span className="text-xs tabular-nums text-muted-foreground">
        {index + 1} / {ids.length}
      </span>
      {older ? (
        <Button asChild variant="outline" size="sm">
          <Link href={href(older)}>
            {t("older")}
            <ChevronRightIcon />
          </Link>
        </Button>
      ) : (
        <span />
      )}
    </nav>
  );
}
