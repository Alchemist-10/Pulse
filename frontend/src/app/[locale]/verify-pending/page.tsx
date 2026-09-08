"use client";

import { Suspense, useState } from "react";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Callout } from "@/components/ui/Callout";
import { Link } from "@/i18n/navigation";
import { api } from "@/lib/api";
import { useApiErrorMessage } from "@/lib/errors";

function VerifyPending() {
  const t = useTranslations("auth");
  const errorMessage = useApiErrorMessage();
  const email = useSearchParams().get("email") ?? "";

  const [status, setStatus] = useState<"idle" | "sending" | "sent">("idle");
  const [error, setError] = useState<string | null>(null);

  async function resend() {
    if (!email) return;
    setStatus("sending");
    setError(null);
    try {
      await api.post("/auth/verify/resend", { email });
      setStatus("sent");
    } catch (err) {
      setError(errorMessage(err));
      setStatus("idle");
    }
  }

  return (
    <section className="mx-auto max-w-sm space-y-6">
      <h1 className="text-2xl font-bold text-foreground">
        {t("verifyPending.title")}
      </h1>

      <p className="text-sm text-muted">
        {email
          ? t("verifyPending.body", { email })
          : t("verifyPending.bodyNoEmail")}
      </p>

      {status === "sent" && (
        <Callout tone="success" iconLabel={t("verifyPending.title")}>
          {t("verifyPending.resent")}
        </Callout>
      )}
      {error && (
        <Callout tone="error" iconLabel={t("verifyPending.title")}>
          {error}
        </Callout>
      )}

      {email && (
        <Button
          variant="secondary"
          loading={status === "sending"}
          onClick={resend}
          className="w-full"
        >
          {t("verifyPending.resend")}
        </Button>
      )}

      <p className="text-sm">
        <Link href="/login" className="font-medium text-accent-text underline">
          {t("verifyPending.backToLogin")}
        </Link>
      </p>
    </section>
  );
}

export default function VerifyPendingPage() {
  // useSearchParams needs a Suspense boundary in the App Router.
  return (
    <Suspense>
      <VerifyPending />
    </Suspense>
  );
}
