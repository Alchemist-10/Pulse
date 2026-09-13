"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Callout } from "@/components/ui/Callout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Link, useRouter } from "@/i18n/navigation";
import { api, ApiError } from "@/lib/api";
import type { Me } from "@/lib/auth";

// Administrator-only entry point (issue #55). An Administrator reads no
// clinical data on any endpoint, ever (ADR-0007) — this dashboard and
// everything under `/admin` only ever surfaces identity fields and counts.
//
// Route protection: the backend already refuses every `/api/v1/admin/*`
// call to a non-Administrator with FORBIDDEN (`Permission.ADMIN_DUPLICATE_REVIEW`,
// enforced server-side and the only real guard). This client-side check exists
// only so a non-admin sees a clear message instead of a broken screen — there
// is no existing client-side role-gating convention elsewhere in the app to
// follow (every other protected screen relies solely on the backend's 401/404),
// so this is a new, minimal pattern: fetch `/auth/me`, compare `role`.
type GateState =
  | { status: "loading" }
  | { status: "denied" }
  | { status: "error"; message: string }
  | { status: "ready" };

export default function AdminDashboardPage() {
  const t = useTranslations("admin");
  const router = useRouter();
  const [gate, setGate] = useState<GateState>({ status: "loading" });

  useEffect(() => {
    let active = true;
    api
      .get<Me>("/auth/me")
      .then((me) => {
        if (!active) return;
        setGate(me.role === "ADMINISTRATOR" ? { status: "ready" } : { status: "denied" });
      })
      .catch((err) => {
        if (!active) return;
        if (err instanceof ApiError && (err.status === 401 || err.code === "SESSION_EXPIRED")) {
          router.replace("/login");
          return;
        }
        setGate({ status: "error", message: t("gate.error") });
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (gate.status === "loading") {
    return <p className="text-sm text-muted">{t("loading")}</p>;
  }
  if (gate.status === "denied") {
    return (
      <Callout tone="error" iconLabel={t("gate.title")}>
        {t("gate.denied")}
      </Callout>
    );
  }
  if (gate.status === "error") {
    return (
      <Callout tone="error" iconLabel={t("gate.title")}>
        {gate.message}
      </Callout>
    );
  }

  return (
    <section className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-foreground">{t("title")}</h1>
        <p className="text-sm text-muted">{t("subtitle")}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("duplicateReview.title")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted">{t("duplicateReview.description")}</p>
          <Link
            href="/admin/duplicates"
            className="inline-flex min-h-11 items-center rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-contrast shadow-sm transition-colors hover:bg-accent-hover"
          >
            {t("duplicateReview.cta")}
          </Link>
        </CardContent>
      </Card>
    </section>
  );
}
