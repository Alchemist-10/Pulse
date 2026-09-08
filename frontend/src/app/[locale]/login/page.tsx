"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/Button";
import { Callout } from "@/components/ui/Callout";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { Link, useRouter } from "@/i18n/navigation";
import { api } from "@/lib/api";
import { useApiErrorMessage } from "@/lib/errors";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

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
      router.push("/profile");
    } catch (err) {
      setFormError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="mx-auto max-w-sm space-y-6">
      <h1 className="text-2xl font-bold text-foreground">{t("login.title")}</h1>

      {formError && (
        <Callout tone="error" iconLabel={t("login.title")}>
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
    </section>
  );
}
