"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/Button";
import { Callout } from "@/components/ui/Callout";
import { Card, CardContent } from "@/components/ui/Card";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { Link, useRouter } from "@/i18n/navigation";
import { api } from "@/lib/api";
import type { Me } from "@/lib/auth";
import { useApiErrorMessage } from "@/lib/errors";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Seeded dev accounts (seed/scripts/build.py `_mark_demo_logins` /
// `build_providers`, DEV_PASSWORD in seed/scripts/common.py). Real rows from
// the committed seed dataset — never invented — so the buttons below only
// ever fill the form; the actual login still goes through normal validation
// and `/auth/login`.
const DEMO_PASSWORD = "Pulse@demo1";
const DEMO_ACCOUNTS = [
  { role: "Patient (EN)", email: "demo.patient.en@example.com" },
  { role: "Patient (HI)", email: "demo.patient.hi@example.com" },
  { role: "Provider staff", email: "staff000@example.com" },
  { role: "Clinician", email: "clinician0@example.com" },
] as const;

export default function LoginPage() {
  const t = useTranslations("auth");
  const errorMessage = useApiErrorMessage();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);

    const next: Record<string, string> = {};
    if (!email) next.email = t("validation.emailRequired");
    else if (!EMAIL_RE.test(email)) next.email = t("validation.emailInvalid");
    if (!password) next.password = t("validation.passwordRequired");
    setErrors(next);
    if (Object.keys(next).length > 0) return;

    setSubmitting(true);
    try {
      // Session cookie is set by the response; nothing to read from the body.
      await api.post("/auth/login", { email, password });
      // Administrators have no Patient profile to land on (ADR-0007) — send
      // them to the admin dashboard instead. Every other role keeps landing
      // on /profile, unchanged.
      const me = await api.get<Me>("/auth/me");
      router.push(me.role === "ADMINISTRATOR" ? "/admin" : "/profile");
    } catch (err) {
      setFormError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  function fillDemo(account: (typeof DEMO_ACCOUNTS)[number]) {
    setEmail(account.email);
    setPassword(DEMO_PASSWORD);
    setErrors({});
    setFormError(null);
  }

  return (
    <section className="mx-auto max-w-sm space-y-6">
      <div className="space-y-1 text-center">
        <h1 className="text-2xl font-bold text-foreground">{t("login.title")}</h1>
      </div>

      {formError && (
        <Callout tone="error" iconLabel={t("login.title")}>
          {formError}
        </Callout>
      )}

      <Card>
        <CardContent className="space-y-4 pt-5">
          <form onSubmit={onSubmit} noValidate className="space-y-4">
            <FormField label={t("fields.email")} error={errors.email}>
              {(props) => (
                <Input
                  {...props}
                  type="email"
                  autoComplete="email"
                  inputMode="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              )}
            </FormField>

            <FormField label={t("fields.password")} error={errors.password}>
              {(props) => (
                <Input
                  {...props}
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              )}
            </FormField>

            <Button type="submit" loading={submitting} className="w-full">
              {t("login.submit")}
            </Button>
          </form>

          <p className="text-sm text-muted">
            {t("login.noAccount")}{" "}
            <Link href="/register" className="font-medium text-accent-text underline">
              {t("login.registerLink")}
            </Link>
          </p>
        </CardContent>
      </Card>

      {/* Demo affordance only — deliberately styled apart from the real
          login card above (dashed border, muted surface) so it never reads
          as part of production auth. Buttons only prefill the real form's
          fields; submission still goes through normal validation and
          `/auth/login`, never bypassed. */}
      <div className="space-y-3 rounded-xl border border-dashed border-border-strong bg-surface-raised p-4">
        <div className="space-y-0.5">
          <p className="text-xs font-semibold tracking-wide text-muted uppercase">
            Demo credentials
          </p>
          <p className="text-xs text-muted">
            Seeded accounts from the demo dataset — password is the same for all.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {DEMO_ACCOUNTS.map((account) => (
            <Button
              key={account.email}
              type="button"
              variant="secondary"
              className="min-h-9 flex-col items-start gap-0 py-1.5 text-left"
              onClick={() => fillDemo(account)}
            >
              <span className="text-xs font-semibold text-foreground">{account.role}</span>
              <span className="truncate text-[11px] font-normal text-muted">
                {account.email}
              </span>
            </Button>
          ))}
        </div>
      </div>
    </section>
  );
}
