"use client";

import { use, useEffect, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { BackButton } from "@/components/BackButton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, ApiError } from "@/lib/api";
import { useApiErrorMessage } from "@/lib/errors";
import { formatDate } from "@/lib/format";
import type { AdminPatientDetail } from "@/lib/generated/api";

// Identity + counts only (ADR-0007). No entry content, no consent scope.
export default function AdminPatientPage({
  params,
}: {
  params: Promise<{ patientId: string }>;
}) {
  const { patientId } = use(params);
  const t = useTranslations("admin.directory");
  const locale = useLocale();
  const errorMessage = useApiErrorMessage();
  const [patient, setPatient] = useState<AdminPatientDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api
      .get<AdminPatientDetail>(`/admin/patients/${patientId}`)
      .then((p) => active && setPatient(p))
      .catch(
        (e) =>
          active &&
          setError(
            e instanceof ApiError && e.status === 404
              ? t("detail.notFound")
              : errorMessage(e),
          ),
      );
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId]);

  const rows: [string, string | number][] = patient
    ? [
        [t("cols.dob"), patient.dateOfBirth ? formatDate(patient.dateOfBirth) : "—"],
        [t("detail.sex"), patient.sex ?? "—"],
        [t("cols.phone"), patient.phone ?? "—"],
        [
          t("detail.address"),
          [patient.addressLine, patient.city, patient.state]
            .filter(Boolean)
            .join(", ") || "—",
        ],
        [t("detail.locale"), patient.localePreference],
        [t("cols.account"), patient.claimed ? t("claimed") : t("unclaimed")],
        [
          t("cols.registered"),
          new Date(patient.createdAt).toLocaleDateString(`${locale}-IN`),
        ],
        [t("cols.records"), patient.entryCount],
        [t("detail.activeConsents"), patient.activeConsentCount],
        [t("detail.totalConsents"), patient.totalConsentCount],
        [t("detail.auditEvents"), patient.auditEventCount],
      ]
    : [];

  return (
    <section className="mx-auto max-w-2xl space-y-5">
      <BackButton fallback="/admin" />
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {patient && (
        <Card>
          <CardHeader>
            <CardTitle role="heading" aria-level={1}>
              {patient.fullName}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-xs text-muted-foreground">
              {t("detail.note")}
            </p>
            <dl className="grid gap-3 sm:grid-cols-2">
              {rows.map(([label, value]) => (
                <div key={label}>
                  <dt className="text-xs text-muted-foreground">{label}</dt>
                  <dd className="text-sm font-medium break-words">{value}</dd>
                </div>
              ))}
            </dl>
          </CardContent>
        </Card>
      )}
    </section>
  );
}
