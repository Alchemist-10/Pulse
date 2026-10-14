import { useTranslations } from "next-intl";
import {
  DropletsIcon,
  HeartPulseIcon,
  NotebookPenIcon,
  PhoneIcon,
  PillIcon,
  ShieldAlertIcon,
  type LucideIcon,
} from "lucide-react";
import { ClinicalText } from "@/components/ClinicalText";

export type CardFields = {
  patientName?: string;
  bloodType: string | null;
  allergies: string | null;
  conditions: string | null;
  medications: string | null;
  nextOfKinName: string | null;
  nextOfKinPhone: string | null;
  nextOfKinRelation: string | null;
  notes: string | null;
};

function Row({
  icon: Icon,
  label,
  children,
}: {
  icon: LucideIcon;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex gap-3 rounded-xl border px-4 py-3">
      <Icon
        aria-hidden="true"
        className="mt-0.5 size-5 shrink-0 text-muted-foreground"
      />
      <div className="min-w-0 space-y-0.5">
        <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
        <dd className="text-sm font-medium whitespace-pre-wrap break-words">
          <ClinicalText>{children}</ClinicalText>
        </dd>
      </div>
    </div>
  );
}

// Clinical text renders as typed by the Patient, never translated.
export function EmergencyCardDisplay({ card }: { card: CardFields }) {
  const t = useTranslations("emergency");
  const kin = [
    card.nextOfKinName,
    card.nextOfKinRelation && `(${card.nextOfKinRelation})`,
  ]
    .filter(Boolean)
    .join(" ");
  const empty =
    !card.bloodType &&
    !card.allergies &&
    !card.conditions &&
    !card.medications &&
    !kin &&
    !card.nextOfKinPhone &&
    !card.notes;
  return (
    <div className="space-y-4">
      {card.patientName && (
        <h2 className="text-xl font-semibold tracking-tight">
          <ClinicalText>{card.patientName}</ClinicalText>
        </h2>
      )}
      {empty ? (
        <p className="text-sm text-muted-foreground">
          {t("view.nothingShared")}
        </p>
      ) : (
        <dl className="grid gap-3 sm:grid-cols-2">
          {card.bloodType && (
            <Row icon={DropletsIcon} label={t("fields.bloodType")}>
              {card.bloodType}
            </Row>
          )}
          {card.allergies && (
            <Row icon={ShieldAlertIcon} label={t("fields.allergies")}>
              {card.allergies}
            </Row>
          )}
          {card.conditions && (
            <Row icon={HeartPulseIcon} label={t("fields.conditions")}>
              {card.conditions}
            </Row>
          )}
          {card.medications && (
            <Row icon={PillIcon} label={t("fields.medications")}>
              {card.medications}
            </Row>
          )}
          {(kin || card.nextOfKinPhone) && (
            <Row icon={PhoneIcon} label={t("fields.nextOfKin")}>
              {kin}
              {card.nextOfKinPhone && (
                <>
                  {kin && <br />}
                  <a
                    href={`tel:${card.nextOfKinPhone}`}
                    className="underline underline-offset-4"
                  >
                    {card.nextOfKinPhone}
                  </a>
                </>
              )}
            </Row>
          )}
          {card.notes && (
            <Row icon={NotebookPenIcon} label={t("fields.notes")}>
              {card.notes}
            </Row>
          )}
        </dl>
      )}
    </div>
  );
}
