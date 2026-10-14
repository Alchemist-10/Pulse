"use client";

import { ArrowLeftIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { useRouter } from "@/i18n/navigation";

// Goes back in history when the user arrived from inside the app, otherwise
// to `fallback`, so a deep link or a fresh tab never dead-ends.
export function BackButton({
  fallback,
  label,
}: {
  fallback: string;
  label?: string;
}) {
  const t = useTranslations("actions");
  const router = useRouter();
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      className="-ml-2 min-h-11"
      onClick={() => {
        if (window.history.length > 1) router.back();
        else router.push(fallback);
      }}
    >
      <ArrowLeftIcon aria-hidden="true" />
      {label ?? t("back")}
    </Button>
  );
}
