"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/Button";
import { Callout } from "@/components/ui/Callout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { useRouter } from "@/i18n/navigation";
import { api, ApiError } from "@/lib/api";
import type { Me } from "@/lib/auth";

// Clinician / Provider-staff landing page (login previously sent every
// non-Administrator role to /profile, which is Patient-only and 403s —
// this is the gap that fix closes). Per docs/demo-script.md, a Clinician
// has no dashboard: they navigate directly to a specific
// /patients/{patientId}/records URL, because a Consent grant is scoped to
// one Patient at a time. This screen is only that navigation step made
// explicit instead of left to a manually-typed URL.
type GateState =
  | { status: "loading" }
  | { status: "denied" }
  | { status: "error" }
  | { status: "ready" };

export default function ClinicianHomePage() {
  const t = useTranslations("clinicianHome");
  const router = useRouter();
  const [gate, setGate] = useState<GateState>({ status: "loading" });
  const [patientId, setPatientId] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api
      .get<Me>("/auth/me")
      .then((me) => {
        if (!active) return;
        setGate(
          me.role === "CLINICIAN" || me.role === "PROVIDER_STAFF"
            ? { status: "ready" }
            : { status: "denied" },
        );
      })
      .catch((err) => {
        if (!active) return;
        if (err instanceof ApiError && (err.status === 401 || err.code === "SESSION_EXPIRED")) {
          router.replace("/login");
          return;
        }
        setGate({ status: "error" });
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const trimmed = patientId.trim();
    if (!trimmed) {
      setError(t("form.validation.required"));
      return;
    }
    router.push(`/patients/${trimmed}/records`);
  }

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
        {t("gate.error")}
      </Callout>
    );
  }

  return (
    <section className="mx-auto max-w-lg space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-foreground">{t("title")}</h1>
        <p className="text-sm text-muted">{t("subtitle")}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("form.title")}</CardTitle>
        </CardHeader>
        <CardContent>
          {error && (
            <Callout tone="error" iconLabel={t("form.title")}>
              {error}
            </Callout>
          )}
          <form onSubmit={onSubmit} noValidate className="space-y-4">
            <FormField label={t("form.fields.patientId")}>
              {(props) => (
                <Input
                  {...props}
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  placeholder={t("form.fields.patientIdPlaceholder")}
                />
              )}
            </FormField>
            <Button type="submit" className="w-full">
              {t("form.submit")}
            </Button>
          </form>
        </CardContent>
      </Card>
    </section>
  );
}
