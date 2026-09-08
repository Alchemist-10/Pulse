"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { Callout } from "@/components/ui/Callout";
import { Link } from "@/i18n/navigation";
import { api, ApiError } from "@/lib/api";

type State = "checking" | "success" | "expired" | "failed" | "missing";

function Verify() {
  const t = useTranslations("auth");
  const params = useSearchParams();
  const challengeId = params.get("challenge");
  const token = params.get("token");

  const [state, setState] = useState<State>(challengeId && token ? "checking" : "missing");
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current || !challengeId || !token) return;
    ran.current = true;
    api
      .post("/auth/verify", { challengeId, token })
      .then(() => setState("success"))
      .catch((err) => {
        if (err instanceof ApiError && err.code === "VERIFICATION_TOKEN_EXPIRED") {
          setState("expired");
        } else {
          setState("failed");
        }
      });
  }, [challengeId, token]);

  const body: Record<State, { tone: "info" | "success" | "error"; text: string }> = {
    checking: { tone: "info", text: t("verify.checking") },
    success: { tone: "success", text: t("verify.success") },
    expired: { tone: "error", text: t("verify.expired") },
    failed: { tone: "error", text: t("verify.failed") },
    missing: { tone: "error", text: t("verify.missingParams") },
  };
  const current = body[state];

  return (
    <section className="mx-auto max-w-sm space-y-6">
      <h1 className="text-2xl font-bold text-foreground">{t("verify.title")}</h1>

      <Callout tone={current.tone} iconLabel={t("verify.title")}>
        {current.text}
      </Callout>

      {state === "success" && (
        <Link
          href="/login"
          className="inline-flex min-h-11 w-full items-center justify-center rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-contrast hover:bg-accent-hover"
        >
          {t("verify.continue")}
        </Link>
      )}
      {(state === "expired" || state === "missing") && (
        <Link
          href="/verify-pending"
          className="inline-flex min-h-11 w-full items-center justify-center rounded-md border border-border-strong bg-surface px-4 py-2 text-sm font-medium text-foreground hover:bg-surface-raised"
        >
          {t("verifyPending.resend")}
        </Link>
      )}
    </section>
  );
}

export default function VerifyPage() {
  return (
    <Suspense>
      <Verify />
    </Suspense>
  );
}
