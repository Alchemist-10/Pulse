"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { useTranslations } from "next-intl";
import { ScanLineIcon } from "lucide-react";
import { QrScanner } from "@/components/QrScanner";
import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useRouter } from "@/i18n/navigation";
import { tokenFromScan } from "@/lib/emergency";

// Shared by the patient's Settings > Scan tab and the clinician's direct
// scan action. Opens `/emergency/{token}`; the server decides what it shows.
export function ScanPanel() {
  const t = useTranslations("emergency.scan");
  const router = useRouter();
  const [active, setActive] = useState(false);
  const [manual, setManual] = useState("");
  const [error, setError] = useState<string | null>(null);

  function open(text: string) {
    const token = tokenFromScan(text);
    if (!token) {
      setActive(false);
      setError(t("invalid"));
      return;
    }
    router.push(`/emergency/${token}`);
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    open(manual);
  }

  return (
    <div className="mx-auto max-w-md space-y-5">
      <p className="text-sm text-muted-foreground">{t("body")}</p>
      {active ? (
        <div className="space-y-3">
          <QrScanner onScan={open} />
          <Button variant="outline" onClick={() => setActive(false)}>
            {t("stop")}
          </Button>
        </div>
      ) : (
        <Button
          onClick={() => {
            setError(null);
            setActive(true);
          }}
        >
          <ScanLineIcon />
          {t("start")}
        </Button>
      )}
      <form onSubmit={submit} noValidate className="space-y-3 border-t pt-4">
        <Field data-invalid={error ? true : undefined}>
          <FieldLabel htmlFor="scan-manual">{t("manual")}</FieldLabel>
          <Input
            id="scan-manual"
            value={manual}
            onChange={(e) => setManual(e.target.value)}
            placeholder={t("manualPlaceholder")}
            aria-invalid={error ? true : undefined}
          />
          {error && <FieldError>{error}</FieldError>}
        </Field>
        <Button type="submit" variant="outline" disabled={!manual.trim()}>
          {t("open")}
        </Button>
      </form>
    </div>
  );
}
