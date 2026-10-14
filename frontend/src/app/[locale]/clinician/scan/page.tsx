"use client";

import { useTranslations } from "next-intl";
import { BackButton } from "@/components/BackButton";
import { ScanPanel } from "@/components/ScanPanel";

export default function ClinicianScanPage() {
  const t = useTranslations("settings");
  return (
    <section className="mx-auto max-w-lg space-y-5">
      <BackButton fallback="/clinician" />
      <h1 className="text-2xl font-semibold tracking-tight">
        {t("tabs.scan")}
      </h1>
      <ScanPanel />
    </section>
  );
}
