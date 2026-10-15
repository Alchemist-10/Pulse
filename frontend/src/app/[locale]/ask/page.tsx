"use client";

import { useTranslations } from "next-intl";
import { AskChat } from "@/components/AskChat";
import { BackButton } from "@/components/BackButton";

export default function AskPage() {
  const t = useTranslations("ask");
  return (
    <div className="mx-auto w-full max-w-2xl space-y-6">
      <BackButton fallback="/timeline" />
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight text-balance sm:text-3xl">
          {t("title")}
        </h1>
        <p className="text-sm text-pretty text-muted-foreground">{t("subtitle")}</p>
      </div>
      <AskChat />
    </div>
  );
}
