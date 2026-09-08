"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/Button";
import { Callout } from "@/components/ui/Callout";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Link, useRouter } from "@/i18n/navigation";
import { api } from "@/lib/api";
import { fieldErrorsFrom, useApiErrorMessage } from "@/lib/errors";

const ROLES = ["PATIENT", "CLINICIAN", "PROVIDER_STAFF", "ADMINISTRATOR"] as const;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD = 12;

export default function RegisterPage() {
  const t = useTranslations("auth");
  const errorMessage = useApiErrorMessage();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<string>("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function validate(): Record<string, string> {
    const next: Record<string, string> = {};
    if (!email) next.email = t("validation.emailRequired");
    else if (!EMAIL_RE.test(email)) next.email = t("validation.emailInvalid");
    if (!password) next.password = t("validation.passwordRequired");
    else if (password.length < MIN_PASSWORD)
      next.password = t("validation.passwordTooShort");
    if (!role) next.role = t("validation.roleRequired");
    return next;
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    const found = validate();
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    setSubmitting(true);
    try {
      await api.post("/auth/register", { email, password, role });
      router.push(`/verify-pending?email=${encodeURIComponent(email)}`);
    } catch (err) {
      const fieldErrors = fieldErrorsFrom(err);
      if (Object.keys(fieldErrors).length > 0) setErrors(fieldErrors);
      setFormError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="mx-auto max-w-sm space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-foreground">{t("register.title")}</h1>
        <p className="text-sm text-muted">{t("register.subtitle")}</p>
      </div>

      {formError && (
        <Callout tone="error" iconLabel={t("register.title")}>
          {formError}
        </Callout>
      )}

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
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          )}
        </FormField>

        <FormField label={t("fields.role")} error={errors.role}>
          {(props) => (
            <Select
              {...props}
              value={role || undefined}
              onValueChange={setRole}
              placeholder={t("fields.role")}
              options={ROLES.map((value) => ({
                value,
                label: t(`roles.${value}`),
              }))}
            />
          )}
        </FormField>

        <Button type="submit" loading={submitting} className="w-full">
          {t("register.submit")}
        </Button>
      </form>

      <p className="text-sm text-muted">
        {t("register.haveAccount")}{" "}
        <Link href="/login" className="font-medium text-accent-text underline">
          {t("register.signInLink")}
        </Link>
      </p>
    </section>
  );
}
