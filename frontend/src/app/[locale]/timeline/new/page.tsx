"use client";

import { useId, useState } from "react";
import type { FormEvent } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/Button";
import { Callout } from "@/components/ui/Callout";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Link } from "@/i18n/navigation";
import { api } from "@/lib/api";
import { useApiErrorMessage, useFieldErrors } from "@/lib/errors";
import {
  ENTRY_TYPES,
  uploadDocument,
  type EntryCreate,
  type EntryType,
} from "@/lib/records";

const CODED_TYPES = new Set<EntryType>(["DIAGNOSIS", "PROCEDURE", "LAB_REPORT"]);

// Provider Staff files an Entry for any Patient (clinical-safety.md:
// `patient.user_id` is nullable and load-bearing — a Patient need not have
// registered). There is no patient search screen yet, so the id is a plain
// field rather than an unbuilt picker (ponytail: no speculative UI).
export default function NewEntryPage() {
  const t = useTranslations("entry");
  const tTimeline = useTranslations("timeline");
  const errorMessage = useApiErrorMessage();
  const fieldErrors = useFieldErrors();
  const formId = useId();

  const [patientId, setPatientId] = useState("");
  const [entryType, setEntryType] = useState<EntryType | "">("");
  const [occurredAt, setOccurredAt] = useState("");
  const [isCritical, setIsCritical] = useState(false);
  const [codeSystem, setCodeSystem] = useState("");
  const [code, setCode] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [valueNumeric, setValueNumeric] = useState("");
  const [valueText, setValueText] = useState("");
  const [unit, setUnit] = useState("");
  const [referenceLow, setReferenceLow] = useState("");
  const [referenceHigh, setReferenceHigh] = useState("");
  const [medicationName, setMedicationName] = useState("");
  const [dosage, setDosage] = useState("");
  const [frequency, setFrequency] = useState("");
  const [route, setRoute] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [uploadFraction, setUploadFraction] = useState<number | null>(null);
  const [createdId, setCreatedId] = useState<string | null>(null);

  const f = t.raw("new.fields") as Record<string, string>;

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    setErrors({});

    if (!patientId || !entryType || !occurredAt) {
      setFormError(t("new.validation.requiredFields"));
      return;
    }

    const parsedOccurredAt = new Date(occurredAt);
    if (Number.isNaN(parsedOccurredAt.getTime())) {
      setFormError(t("new.validation.requiredFields"));
      return;
    }

    const payload: EntryCreate = {
      entryType,
      occurredAt: parsedOccurredAt.toISOString(),
      isCritical,
      codeSystem: codeSystem || null,
      code: code || null,
      displayName: displayName || null,
      valueNumeric: valueNumeric ? Number(valueNumeric) : null,
      valueText: valueText || null,
      unit: unit || null,
      referenceLow: referenceLow ? Number(referenceLow) : null,
      referenceHigh: referenceHigh ? Number(referenceHigh) : null,
      medicationName: medicationName || null,
      dosage: dosage || null,
      frequency: frequency || null,
      route: route || null,
      text: text || null,
    };

    setSubmitting(true);
    try {
      const entry = await api.post<{ id: string }>(`/patients/${patientId}/entries`, payload);
      setCreatedId(entry.id);

      if (file) {
        setUploadFraction(0);
        try {
          await uploadDocument(patientId, entry.id, file, setUploadFraction);
        } catch (err) {
          setFormError(t("new.upload.failed", { reason: errorMessage(err) }));
        } finally {
          setUploadFraction(null);
        }
      }
    } catch (err) {
      const fields = fieldErrors(err);
      if (Object.keys(fields).length > 0) setErrors(fields);
      setFormError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (createdId) {
    return (
      <section className="mx-auto max-w-lg space-y-4">
        <Callout tone="success" iconLabel={t("new.success.title")}>
          {formError ?? t("new.success.body")}
        </Callout>
        <Link href={`/timeline/${createdId}`} className="text-sm font-medium text-accent-text underline">
          {t("new.success.viewEntry")}
        </Link>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-lg space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-foreground">{t("new.title")}</h1>
        <p className="text-sm text-muted">{t("new.subtitle")}</p>
      </div>

      {formError && (
        <Callout tone="error" iconLabel={t("new.title")}>
          {formError}
        </Callout>
      )}

      <form onSubmit={onSubmit} noValidate className="space-y-4">
        <FormField label={f.patientId} error={errors.patientId}>
          {(props) => (
            <Input {...props} value={patientId} onChange={(e) => setPatientId(e.target.value)} />
          )}
        </FormField>

        <FormField label={f.entryType} error={errors.entryType}>
          {(props) => (
            <Select
              {...props}
              value={entryType || undefined}
              onValueChange={(value) => setEntryType(value as EntryType)}
              placeholder={f.entryType}
              options={ENTRY_TYPES.map((type) => ({
                value: type,
                label: tTimeline(`entryTypes.${type}`),
              }))}
            />
          )}
        </FormField>

        <FormField label={f.occurredAt} error={errors.occurredAt}>
          {(props) => (
            <Input
              {...props}
              type="datetime-local"
              value={occurredAt}
              onChange={(e) => setOccurredAt(e.target.value)}
            />
          )}
        </FormField>

        <div className="flex items-center gap-2">
          <input
            id={`${formId}-critical`}
            type="checkbox"
            checked={isCritical}
            onChange={(e) => setIsCritical(e.target.checked)}
            className="size-4 rounded border-border-strong"
          />
          <label htmlFor={`${formId}-critical`} className="text-sm text-foreground">
            {f.isCritical}
          </label>
        </div>

        {entryType && CODED_TYPES.has(entryType) && (
          <>
            <FormField label={f.codeSystem} error={errors.codeSystem}>
              {(props) => (
                <Input {...props} value={codeSystem} onChange={(e) => setCodeSystem(e.target.value)} />
              )}
            </FormField>
            <FormField label={f.code} error={errors.code}>
              {(props) => <Input {...props} value={code} onChange={(e) => setCode(e.target.value)} />}
            </FormField>
            <FormField label={f.displayName} error={errors.displayName}>
              {(props) => (
                <Input
                  {...props}
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                />
              )}
            </FormField>
          </>
        )}

        {entryType === "LAB_REPORT" && (
          <>
            <FormField label={f.valueNumeric} error={errors.valueNumeric}>
              {(props) => (
                <Input
                  {...props}
                  type="number"
                  inputMode="decimal"
                  value={valueNumeric}
                  onChange={(e) => setValueNumeric(e.target.value)}
                />
              )}
            </FormField>
            <FormField label={f.valueText} error={errors.valueText}>
              {(props) => (
                <Input {...props} value={valueText} onChange={(e) => setValueText(e.target.value)} />
              )}
            </FormField>
            <FormField label={f.unit} error={errors.unit}>
              {(props) => <Input {...props} value={unit} onChange={(e) => setUnit(e.target.value)} />}
            </FormField>
            <FormField label={f.referenceLow} error={errors.referenceLow}>
              {(props) => (
                <Input
                  {...props}
                  type="number"
                  inputMode="decimal"
                  value={referenceLow}
                  onChange={(e) => setReferenceLow(e.target.value)}
                />
              )}
            </FormField>
            <FormField label={f.referenceHigh} error={errors.referenceHigh}>
              {(props) => (
                <Input
                  {...props}
                  type="number"
                  inputMode="decimal"
                  value={referenceHigh}
                  onChange={(e) => setReferenceHigh(e.target.value)}
                />
              )}
            </FormField>
          </>
        )}

        {entryType === "PRESCRIPTION" && (
          <>
            <FormField label={f.medicationName} error={errors.medicationName}>
              {(props) => (
                <Input
                  {...props}
                  value={medicationName}
                  onChange={(e) => setMedicationName(e.target.value)}
                />
              )}
            </FormField>
            <FormField label={f.dosage} error={errors.dosage}>
              {(props) => <Input {...props} value={dosage} onChange={(e) => setDosage(e.target.value)} />}
            </FormField>
            <FormField label={f.frequency} error={errors.frequency}>
              {(props) => (
                <Input {...props} value={frequency} onChange={(e) => setFrequency(e.target.value)} />
              )}
            </FormField>
            <FormField label={f.route} error={errors.route}>
              {(props) => <Input {...props} value={route} onChange={(e) => setRoute(e.target.value)} />}
            </FormField>
          </>
        )}

        {entryType === "CLINICAL_NOTE" && (
          <FormField label={f.text} error={errors.text}>
            {(props) => (
              <textarea
                {...props}
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={5}
                className="block w-full rounded-md border border-border-strong bg-surface px-3 py-2 text-sm text-foreground outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-1 focus-visible:ring-offset-background"
              />
            )}
          </FormField>
        )}

        <div className="space-y-1.5">
          <label htmlFor={`${formId}-file`} className="block text-sm font-medium text-foreground">
            {f.file}
          </label>
          <p className="text-xs text-muted">{t("new.fileHint")}</p>
          <input
            id={`${formId}-file`}
            type="file"
            accept="application/pdf,image/png,image/jpeg"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-foreground"
          />
        </div>

        {uploadFraction != null && (
          <div className="space-y-1">
            <p className="text-xs text-muted">
              {t("new.upload.inProgress", { percent: Math.round(uploadFraction * 100) })}
            </p>
            <div
              role="progressbar"
              aria-valuenow={Math.round(uploadFraction * 100)}
              aria-valuemin={0}
              aria-valuemax={100}
              className="h-2 w-full overflow-hidden rounded-full bg-surface-raised"
            >
              <div
                className="h-full bg-accent transition-[width]"
                style={{ width: `${Math.round(uploadFraction * 100)}%` }}
              />
            </div>
          </div>
        )}

        <Button type="submit" loading={submitting} className="w-full">
          {submitting ? t("new.submitting") : t("new.submit")}
        </Button>
      </form>
    </section>
  );
}
