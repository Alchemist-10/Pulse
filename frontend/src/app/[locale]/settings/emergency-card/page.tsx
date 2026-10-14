"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useLocale, useTranslations } from "next-intl";
import QRCode from "qrcode";
import {
  DownloadIcon,
  PrinterIcon,
  QrCodeIcon,
  RefreshCwIcon,
} from "lucide-react";
import { toast } from "sonner";
import { EmergencyCardDisplay } from "@/components/EmergencyCardDisplay";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { useApiErrorMessage } from "@/lib/errors";
import { emergencyLink, type EmergencyCard } from "@/lib/emergency";

type FieldKey =
  | "bloodType"
  | "allergies"
  | "conditions"
  | "medications"
  | "nextOfKin"
  | "notes";

type Draft = {
  bloodType: string;
  allergies: string;
  conditions: string;
  medications: string;
  nextOfKinName: string;
  nextOfKinPhone: string;
  nextOfKinRelation: string;
  notes: string;
  show: Record<FieldKey, boolean>;
};

const toDraft = (c: EmergencyCard): Draft => ({
  bloodType: c.bloodType ?? "",
  allergies: c.allergies ?? "",
  conditions: c.conditions ?? "",
  medications: c.medications ?? "",
  nextOfKinName: c.nextOfKinName ?? "",
  nextOfKinPhone: c.nextOfKinPhone ?? "",
  nextOfKinRelation: c.nextOfKinRelation ?? "",
  notes: c.notes ?? "",
  show: {
    bloodType: c.showBloodType,
    allergies: c.showAllergies,
    conditions: c.showConditions,
    medications: c.showMedications,
    nextOfKin: c.showNextOfKin,
    notes: c.showNotes,
  },
});

const orNull = (v: string) => (v.trim() ? v.trim() : null);

export default function EmergencyCardSettingsPage() {
  const t = useTranslations("emergency");
  const locale = useLocale();
  const errorMessage = useApiErrorMessage();
  const [card, setCard] = useState<EmergencyCard | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [qr, setQr] = useState<string | null>(null);
  const [busyQr, setBusyQr] = useState(false);
  const qrLink = useRef<string | null>(null);

  useEffect(() => {
    let active = true;
    api
      .get<EmergencyCard>("/emergency-card")
      .then((c) => {
        if (!active) return;
        setCard(c);
        setDraft(toDraft(c));
      })
      .catch((e) => active && setError(errorMessage(e)));
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    let active = true;
    if (!card?.qrToken) {
      qrLink.current = null;
      Promise.resolve().then(() => active && setQr(null));
      return;
    }
    const link = emergencyLink(window.location.origin, locale, card.qrToken);
    qrLink.current = link;
    QRCode.toDataURL(link, { width: 320, margin: 2, errorCorrectionLevel: "M" })
      .then((url) => active && setQr(url))
      .catch(() => active && setQr(null));
    return () => {
      active = false;
    };
  }, [card?.qrToken, locale]);

  if (!draft) {
    return error ? (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    ) : (
      <p className="text-sm text-muted-foreground">{t("loading")}</p>
    );
  }

  const set = (patch: Partial<Draft>) => setDraft({ ...draft, ...patch });
  const setShow = (key: FieldKey, value: boolean) =>
    setDraft({ ...draft, show: { ...draft.show, [key]: value } });

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!draft) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await api.put<EmergencyCard>("/emergency-card", {
        bloodType: orNull(draft.bloodType),
        allergies: orNull(draft.allergies),
        conditions: orNull(draft.conditions),
        medications: orNull(draft.medications),
        nextOfKinName: orNull(draft.nextOfKinName),
        nextOfKinPhone: orNull(draft.nextOfKinPhone),
        nextOfKinRelation: orNull(draft.nextOfKinRelation),
        notes: orNull(draft.notes),
        showBloodType: draft.show.bloodType,
        showAllergies: draft.show.allergies,
        showConditions: draft.show.conditions,
        showMedications: draft.show.medications,
        showNextOfKin: draft.show.nextOfKin,
        showNotes: draft.show.notes,
      });
      setCard(updated);
      setDraft(toDraft(updated));
      toast.success(t("saved"));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setSaving(false);
    }
  }

  async function qrAction(method: "post" | "delete") {
    setBusyQr(true);
    setError(null);
    try {
      const updated =
        method === "post"
          ? await api.post<EmergencyCard>("/emergency-card/qr")
          : await api.delete<EmergencyCard>("/emergency-card/qr");
      setCard(updated);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusyQr(false);
    }
  }

  function download() {
    if (!qr) return;
    const a = document.createElement("a");
    a.href = qr;
    a.download = "pulse-emergency-qr.png";
    a.click();
  }

  const toggle = (key: FieldKey) => (
    <label className="flex items-center gap-2 text-sm text-muted-foreground">
      <Switch
        checked={draft.show[key]}
        onCheckedChange={(v) => setShow(key, v)}
        aria-label={t("shareToggle")}
      />
      {draft.show[key] ? t("shared") : t("hidden")}
    </label>
  );

  const block = (key: FieldKey, label: string, control: React.ReactNode) => (
    <Field>
      <div className="flex items-center justify-between gap-3">
        <FieldLabel htmlFor={`ec-${key}`}>{label}</FieldLabel>
        {toggle(key)}
      </div>
      {control}
    </Field>
  );

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <form onSubmit={save} className="space-y-5">
        <p className="text-sm text-muted-foreground">{t("intro")}</p>
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {block(
          "bloodType",
          t("fields.bloodType"),
          <Input
            id="ec-bloodType"
            value={draft.bloodType}
            maxLength={16}
            onChange={(e) => set({ bloodType: e.target.value })}
          />,
        )}
        {block(
          "allergies",
          t("fields.allergies"),
          <Textarea
            id="ec-allergies"
            rows={2}
            value={draft.allergies}
            maxLength={2000}
            onChange={(e) => set({ allergies: e.target.value })}
          />,
        )}
        {block(
          "conditions",
          t("fields.conditions"),
          <Textarea
            id="ec-conditions"
            rows={2}
            value={draft.conditions}
            maxLength={2000}
            onChange={(e) => set({ conditions: e.target.value })}
          />,
        )}
        {block(
          "medications",
          t("fields.medications"),
          <Textarea
            id="ec-medications"
            rows={2}
            value={draft.medications}
            maxLength={2000}
            onChange={(e) => set({ medications: e.target.value })}
          />,
        )}
        {block(
          "nextOfKin",
          t("fields.nextOfKin"),
          <div className="grid gap-2 sm:grid-cols-3">
            <Input
              id="ec-nextOfKin"
              aria-label={t("fields.nextOfKinName")}
              placeholder={t("fields.nextOfKinName")}
              value={draft.nextOfKinName}
              maxLength={200}
              onChange={(e) => set({ nextOfKinName: e.target.value })}
            />
            <Input
              aria-label={t("fields.nextOfKinRelation")}
              placeholder={t("fields.nextOfKinRelation")}
              value={draft.nextOfKinRelation}
              maxLength={64}
              onChange={(e) => set({ nextOfKinRelation: e.target.value })}
            />
            <Input
              aria-label={t("fields.nextOfKinPhone")}
              placeholder={t("fields.nextOfKinPhone")}
              inputMode="tel"
              value={draft.nextOfKinPhone}
              maxLength={32}
              onChange={(e) => set({ nextOfKinPhone: e.target.value })}
            />
          </div>,
        )}
        {block(
          "notes",
          t("fields.notes"),
          <Textarea
            id="ec-notes"
            rows={2}
            value={draft.notes}
            maxLength={2000}
            onChange={(e) => set({ notes: e.target.value })}
          />,
        )}
        <Button type="submit" disabled={saving} aria-busy={saving}>
          {saving && <Spinner />}
          {t("save")}
        </Button>
      </form>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("preview.title")}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-xs text-muted-foreground">
              {t("preview.hint")}
            </p>
            <EmergencyCardDisplay
              card={{
                bloodType: draft.show.bloodType
                  ? orNull(draft.bloodType)
                  : null,
                allergies: draft.show.allergies
                  ? orNull(draft.allergies)
                  : null,
                conditions: draft.show.conditions
                  ? orNull(draft.conditions)
                  : null,
                medications: draft.show.medications
                  ? orNull(draft.medications)
                  : null,
                nextOfKinName: draft.show.nextOfKin
                  ? orNull(draft.nextOfKinName)
                  : null,
                nextOfKinPhone: draft.show.nextOfKin
                  ? orNull(draft.nextOfKinPhone)
                  : null,
                nextOfKinRelation: draft.show.nextOfKin
                  ? orNull(draft.nextOfKinRelation)
                  : null,
                notes: draft.show.notes ? orNull(draft.notes) : null,
              }}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <QrCodeIcon aria-hidden="true" className="size-5" />
              {t("qr.title")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">{t("qr.body")}</p>
            {card?.qrToken && qr ? (
              <div className="space-y-3">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={qr}
                  alt={t("qr.alt")}
                  width={240}
                  height={240}
                  className="mx-auto rounded-lg border bg-white p-2"
                />
                <div className="flex flex-wrap justify-center gap-2">
                  <Button variant="outline" size="sm" onClick={download}>
                    <DownloadIcon />
                    {t("qr.download")}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.print()}
                  >
                    <PrinterIcon />
                    {t("qr.print")}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={busyQr}
                    onClick={() => void qrAction("post")}
                  >
                    <RefreshCwIcon />
                    {t("qr.rotate")}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={busyQr}
                    onClick={() => void qrAction("delete")}
                  >
                    {t("qr.disable")}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  {t("qr.rotateHint")}
                </p>
              </div>
            ) : (
              <Button
                disabled={busyQr}
                aria-busy={busyQr}
                onClick={() => void qrAction("post")}
              >
                {busyQr && <Spinner />}
                {t("qr.generate")}
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
