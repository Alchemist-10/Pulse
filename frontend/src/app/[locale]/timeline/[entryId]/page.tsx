"use client";

import { use, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useTranslations } from "next-intl";
import { BreakGlassBanner } from "@/components/BreakGlassBanner";
import { Callout } from "@/components/ui/Callout";
import { ClinicalText } from "@/components/ClinicalText";
import { DocumentViewer } from "@/components/DocumentViewer";
import {
  ClinicalNoteIcon,
  DiagnosisIcon,
  FlaskIcon,
  PrescriptionIcon,
  ProcedureIcon,
} from "@/components/ui/icons";
import { InlineLink } from "@/components/ui/InlineLink";
import { NavLink } from "@/components/ui/NavLink";
import { useRouter } from "@/i18n/navigation";
import { api, ApiError } from "@/lib/api";
import { useApiErrorMessage } from "@/lib/errors";
import { formatDate } from "@/lib/format";
import type { EntryDetail, EntryType } from "@/lib/records";

const ENTRY_ICONS: Record<EntryType, typeof DiagnosisIcon> = {
  DIAGNOSIS: DiagnosisIcon,
  PRESCRIPTION: PrescriptionIcon,
  LAB_REPORT: FlaskIcon,
  PROCEDURE: ProcedureIcon,
  CLINICAL_NOTE: ClinicalNoteIcon,
};

/**
 * "H"/"L" out-of-range flag for a Lab Report. One alert hue (critical/red),
 * never red-versus-green — direction is carried by the ▲/▼ glyph, the
 * letter and the words, not by colour (docs/design-direction.md: "High
 * versus low lab values must not be red versus green").
 */
function labFlag(entry: EntryDetail): "high" | "low" | null {
  if (entry.entryType !== "LAB_REPORT" || entry.valueNumeric == null) return null;
  if (entry.referenceHigh != null && entry.valueNumeric > entry.referenceHigh) return "high";
  if (entry.referenceLow != null && entry.valueNumeric < entry.referenceLow) return "low";
  return null;
}

function AbnormalMarker({ flag }: { flag: "high" | "low" }) {
  const t = useTranslations("timeline");
  const a = t.raw("detail.abnormal") as Record<string, string>;
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-critical-border bg-critical-surface px-2 py-0.5 text-xs font-semibold text-critical">
      <span aria-hidden="true">{flag === "high" ? "▲" : "▼"}</span>
      <span>{flag === "high" ? a.high : a.low}</span>
      <span>{flag === "high" ? a.aboveRange : a.belowRange}</span>
    </span>
  );
}

type LoadState =
  | { status: "loading" }
  | { status: "notFound" }
  | { status: "error"; message: string }
  | { status: "ready"; entry: EntryDetail };

export default function EntryDetailPage({
  params,
}: {
  params: Promise<{ entryId: string }>;
}) {
  const { entryId } = use(params);
  const t = useTranslations("timeline");
  const errorMessage = useApiErrorMessage();
  const router = useRouter();
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let active = true;
    // Deferred one microtask so the reset is a callback, not a direct
    // synchronous setState in the effect body (react-hooks/set-state-in-effect).
    Promise.resolve().then(() => {
      if (active) setState({ status: "loading" });
    });
    api
      .get<EntryDetail>(`/entries/${entryId}`)
      .then((entry) => {
        if (active) setState({ status: "ready", entry });
      })
      .catch((err) => {
        if (!active) return;
        if (err instanceof ApiError && (err.status === 401 || err.code === "SESSION_EXPIRED")) {
          router.replace("/login");
          return;
        }
        if (err instanceof ApiError && err.status === 404) {
          setState({ status: "notFound" });
          return;
        }
        setState({ status: "error", message: errorMessage(err) });
      });
    return () => {
      active = false;
    };
    // errorMessage / router are stable for the page lifetime.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entryId]);

  return (
    <section className="space-y-6">
      <NavLink href="/timeline" icon="back">
        {t("detail.back")}
      </NavLink>

      {state.status === "loading" && <p className="text-sm text-muted">{t("loading")}</p>}

      {state.status === "notFound" && (
        <Callout tone="info" iconLabel={t("detail.title")}>
          {t("detail.notFound")}
        </Callout>
      )}

      {state.status === "error" && (
        <Callout tone="error" iconLabel={t("error.title")}>
          {state.message}
        </Callout>
      )}

      {state.status === "ready" && (
        <>
          <BreakGlassBanner patientId={state.entry.patientId} />
          <EntryDetailView entry={state.entry} />
        </>
      )}
    </section>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-1 gap-1 px-4 py-3 sm:grid-cols-3 sm:gap-4">
      <dt className="text-sm font-medium text-muted">{label}</dt>
      <dd className="text-sm text-foreground sm:col-span-2">{children}</dd>
    </div>
  );
}

function EntryDetailView({ entry }: { entry: EntryDetail }) {
  const t = useTranslations("timeline");
  const Icon = ENTRY_ICONS[entry.entryType];
  const f = t.raw("detail.fields") as Record<string, string>;

  const rows: Array<[string, ReactNode]> = [
    [f.occurredAt, formatDate(entry.occurredAt)],
    [f.recordedAt, formatDate(entry.recordedAt)],
  ];

  if (entry.code || entry.displayName) {
    rows.push([
      f.code,
      <ClinicalText key="code">
        {entry.displayName ?? "—"}
        {entry.code ? ` (${entry.codeSystem ?? ""} ${entry.code})` : ""}
      </ClinicalText>,
    ]);
  }
  if (entry.entryType === "LAB_REPORT") {
    const value = entry.valueNumeric != null ? String(entry.valueNumeric) : entry.valueText;
    const flag = labFlag(entry);
    rows.push([
      f.value,
      <span key="value" className="flex flex-wrap items-center gap-2">
        <ClinicalText>
          {value ?? "—"} {entry.unit ?? ""}
        </ClinicalText>
        {flag && <AbnormalMarker flag={flag} />}
      </span>,
    ]);
    if (entry.referenceLow != null || entry.referenceHigh != null) {
      rows.push([
        f.referenceRange,
        <ClinicalText key="range">
          {entry.referenceLow ?? "—"} – {entry.referenceHigh ?? "—"} {entry.unit ?? ""}
        </ClinicalText>,
      ]);
    }
  }
  if (entry.entryType === "PRESCRIPTION") {
    rows.push([f.medication, <ClinicalText key="med">{entry.medicationName ?? "—"}</ClinicalText>]);
    if (entry.dosage) rows.push([f.dosage, <ClinicalText key="dosage">{entry.dosage}</ClinicalText>]);
    if (entry.frequency)
      rows.push([f.frequency, <ClinicalText key="freq">{entry.frequency}</ClinicalText>]);
    if (entry.route) rows.push([f.route, <ClinicalText key="route">{entry.route}</ClinicalText>]);
  }
  if (entry.entryType === "CLINICAL_NOTE" && entry.text) {
    rows.push([f.note, <ClinicalText key="note">{entry.text}</ClinicalText>]);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Icon className="size-6 shrink-0 text-muted" />
        <h1 className="text-2xl font-bold text-foreground">
          {t(`entryTypes.${entry.entryType}`)}
        </h1>
      </div>

      {entry.supersedesId && (
        <Callout tone="info" iconLabel={t("detail.title")}>
          <span>{t("detail.correctsNotice")}</span>{" "}
          <InlineLink href={`/timeline/${entry.supersedesId}`}>
            {t("detail.viewPrevious")}
          </InlineLink>
        </Callout>
      )}

      <dl className="divide-y divide-border rounded-xl border border-border bg-surface shadow-sm">
        {rows.map(([label, value]) => (
          <Field key={label} label={label}>
            {value}
          </Field>
        ))}
      </dl>

      {entry.documents.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-muted">{f.documents}</h2>
          <ul className="space-y-2">
            {entry.documents.map((doc) => (
              <DocumentViewer key={doc.id} doc={doc} />
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
