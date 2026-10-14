"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { TriangleAlertIcon } from "lucide-react";
import { BackButton } from "@/components/BackButton";
import { PatientSubNav } from "@/components/PatientSubNav";
import { EmergencyCardDisplay } from "@/components/EmergencyCardDisplay";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { useRouter } from "@/i18n/navigation";
import { api, ApiError } from "@/lib/api";
import type { EmergencyCardView } from "@/lib/emergency";
import { useApiErrorMessage } from "@/lib/errors";

type State =
  | { status: "loading" }
  | { status: "ready"; card: EmergencyCardView }
  | { status: "notFound" }
  | { status: "error"; message: string };

// Not-found and no-consent look identical on purpose (clinical-safety.md).
export function EmergencyCardLoader({
  path,
  fallback,
  recordsPatientId,
}: {
  path: string;
  fallback: string;
  recordsPatientId?: string;
}) {
  const t = useTranslations("emergency.view");
  const router = useRouter();
  const errorMessage = useApiErrorMessage();
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    let active = true;
    api
      .get<EmergencyCardView>(path)
      .then((card) => active && setState({ status: "ready", card }))
      .catch((err) => {
        if (!active) return;
        if (err instanceof ApiError && err.status === 401) {
          router.replace("/login");
        } else if (err instanceof ApiError && err.status === 404) {
          setState({ status: "notFound" });
        } else {
          setState({ status: "error", message: errorMessage(err) });
        }
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path]);

  return (
    <section className="mx-auto max-w-2xl space-y-5">
      {recordsPatientId ? (
        <PatientSubNav patientId={recordsPatientId} active="emergency" />
      ) : (
        <BackButton fallback={fallback} />
      )}
      <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
      {state.status === "loading" && (
        <div className="space-y-3">
          <span className="sr-only">{t("loading")}</span>
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="h-24 w-full" />
        </div>
      )}
      {state.status === "notFound" && (
        <Alert>
          <TriangleAlertIcon />
          <AlertTitle>{t("notFound.title")}</AlertTitle>
          <AlertDescription>{t("notFound.body")}</AlertDescription>
        </Alert>
      )}
      {state.status === "error" && (
        <Alert variant="destructive">
          <TriangleAlertIcon />
          <AlertDescription>{state.message}</AlertDescription>
        </Alert>
      )}
      {state.status === "ready" && (
        <>
          <p className="text-xs text-muted-foreground">{t("audited")}</p>
          <EmergencyCardDisplay
            card={{ ...state.card, patientName: state.card.patientName }}
          />
        </>
      )}
    </section>
  );
}
