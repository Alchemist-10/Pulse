"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { CopyIcon, InfoIcon, UserRoundIcon } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { useRouter } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";
import { api, ApiError } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { useApiErrorMessage } from "@/lib/errors";

// Identity fields only — the patient profile carries no clinical data
// (issue #23, PatientProfile schema; .claude/rules/clinical-safety.md).
import type { PatientProfile } from "@/lib/generated/api";

const EMPTY = "—"; // em dash for a missing identity field

type LoadState =
  | { status: "loading" }
  | { status: "ready"; profile: PatientProfile }
  | { status: "notFound" }
  | { status: "error"; message: string };

function ProfileSkeleton() {
  return (
    <Card aria-hidden="true" className="gap-0 py-0">
      <div className="flex flex-col gap-6 border-b p-6 sm:flex-row sm:items-center sm:p-8">
        <Skeleton className="size-24 shrink-0 rounded-full" />
        <div className="min-w-0 flex-1 space-y-3">
          <Skeleton className="h-8 w-48 max-w-full" />
        </div>
        <div className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-24" />
        </div>
      </div>
      <div className="space-y-3 border-b px-6 py-5 sm:px-8">
        <Skeleton className="h-4 w-24" />
        <div className="flex flex-wrap items-center gap-x-4 gap-y-3">
          <Skeleton className="h-5 w-80 max-w-full" />
          <Skeleton className="h-11 w-32 sm:h-9" />
        </div>
        <Skeleton className="h-10 w-full max-w-lg sm:h-4" />
      </div>
      <div className="grid gap-8 p-6 sm:p-8 lg:grid-cols-2 lg:gap-12">
        {[3, 4].map((count, group) => (
          <div
            key={group}
            className={cn(
              "min-w-0 space-y-5",
              group === 1 &&
                "border-t pt-8 lg:border-t-0 lg:border-l lg:pt-0 lg:pl-12",
            )}
          >
            <Skeleton className="h-6 w-40" />
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              {Array.from({ length: count }).map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    "min-w-0 space-y-1.5",
                    ((group === 0 && i === 2) || (group === 1 && i < 2)) &&
                      "sm:col-span-2",
                  )}
                >
                  <Skeleton className="h-4 w-20 max-w-full" />
                  <Skeleton className="h-6 w-28 max-w-full" />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function ProfileField({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div className={cn("min-w-0 space-y-1.5", className)}>
      <dt className="text-sm leading-relaxed text-muted-foreground">{label}</dt>
      <dd className="text-base leading-relaxed font-medium text-foreground [overflow-wrap:anywhere]">
        {value}
      </dd>
    </div>
  );
}

export default function ProfilePage() {
  const t = useTranslations("profile");
  const tLocale = useTranslations("locale");
  const tActions = useTranslations("actions");
  const errorMessage = useApiErrorMessage();
  const router = useRouter();
  const [retryToken, setRetryToken] = useState(0);
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let active = true;
    Promise.resolve().then(() => {
      if (active) setState({ status: "loading" });
    });
    api
      .get<PatientProfile>("/patients/me")
      .then((profile) => {
        if (active) setState({ status: "ready", profile });
      })
      .catch((err) => {
        if (!active) return;
        if (
          err instanceof ApiError &&
          (err.status === 401 || err.code === "SESSION_EXPIRED")
        ) {
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
  }, [retryToken]);

  const header = (
    <div className="space-y-1">
      <h1 className="workspace-heading">{t("title")}</h1>
      <p className="text-sm text-pretty text-muted-foreground">
        {t("subtitle")}
      </p>
    </div>
  );

  if (state.status === "loading") {
    return (
      <section className="space-y-8">
        {header}
        <span className="sr-only" role="status">
          {t("loading")}
        </span>
        <ProfileSkeleton />
      </section>
    );
  }
  if (state.status === "notFound") {
    return (
      <section className="space-y-8">
        {header}
        <Alert>
          <InfoIcon />
          <AlertTitle>{t("title")}</AlertTitle>
          <AlertDescription>{t("notFound")}</AlertDescription>
        </Alert>
      </section>
    );
  }
  if (state.status === "error") {
    return (
      <section className="space-y-8">
        {header}
        <Alert variant="destructive">
          <InfoIcon />
          <AlertTitle>{t("title")}</AlertTitle>
          <AlertDescription>{state.message}</AlertDescription>
        </Alert>
        <Button variant="outline" onClick={() => setRetryToken((n) => n + 1)}>
          {tActions("retry")}
        </Button>
      </section>
    );
  }

  const { profile } = state;
  const localeLabel = (routing.locales as readonly string[]).includes(
    profile.localePreference,
  )
    ? tLocale(profile.localePreference as (typeof routing.locales)[number])
    : profile.localePreference;

  const show = (value: string | null): string => value?.trim() || EMPTY;

  return (
    <section className="space-y-8">
      {header}

      <Card className="gap-0 py-0">
        <div className="flex flex-col gap-6 border-b p-6 sm:flex-row sm:items-center sm:p-8">
          <div
            aria-hidden="true"
            className="flex size-24 shrink-0 items-center justify-center rounded-full border border-primary/15 bg-primary-soft text-primary"
          >
            <UserRoundIcon className="size-12" strokeWidth={1.5} />
          </div>
          <dl className="min-w-0 flex-1">
            <div>
              <dt className="sr-only">{t("fields.fullName")}</dt>
              <dd>
                <h2 className="text-2xl leading-snug font-semibold tracking-tight text-balance [overflow-wrap:anywhere] sm:text-3xl">
                  {show(profile.fullName)}
                </h2>
              </dd>
            </div>
          </dl>
          <dl className="min-w-0 space-y-2 sm:text-right">
            <dt className="text-sm text-muted-foreground">
              {t("claimed.label")}
            </dt>
            <dd>
              <Badge
                variant="secondary"
                className="h-auto max-w-full px-3 py-1.5 whitespace-normal text-sm leading-relaxed"
              >
                {profile.claimed ? t("claimed.true") : t("claimed.false")}
              </Badge>
            </dd>
          </dl>
        </div>

        <div className="space-y-3 border-b bg-muted/30 px-6 py-5 sm:px-8">
          <dl>
            <dt className="text-sm text-muted-foreground">
              {t("fields.patientId")}
            </dt>
            <dd className="mt-2 flex min-w-0 flex-wrap items-center gap-x-4 gap-y-3">
              <span className="min-w-0 break-all text-sm font-medium text-foreground tabular-nums">
                {profile.id}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(profile.id);
                    toast.success(t("copiedId"));
                  } catch {
                    toast.error(t("copyFailed"));
                  }
                }}
              >
                <CopyIcon className="size-4" aria-hidden="true" />
                {t("copyId")}
              </Button>
            </dd>
          </dl>
          <p className="max-w-prose text-sm leading-relaxed text-muted-foreground">
            {t("patientIdHint")}
          </p>
        </div>

        <div className="grid gap-8 p-6 sm:p-8 lg:grid-cols-2 lg:gap-12">
          <section
            aria-labelledby="profile-personal-heading"
            className="min-w-0 space-y-5"
          >
            <h2
              id="profile-personal-heading"
              className="text-lg font-semibold tracking-tight"
            >
              {t("sections.personal")}
            </h2>
            <dl className="grid grid-cols-1 gap-x-6 gap-y-6 sm:grid-cols-2">
              <ProfileField
                label={t("fields.dateOfBirth")}
                value={formatDate(profile.dateOfBirth) || EMPTY}
              />
              <ProfileField label={t("fields.sex")} value={show(profile.sex)} />
              <ProfileField
                label={t("fields.localePreference")}
                value={localeLabel}
                className="sm:col-span-2"
              />
            </dl>
          </section>
          <section
            aria-labelledby="profile-contact-heading"
            className="min-w-0 space-y-5 border-t pt-8 lg:border-t-0 lg:border-l lg:pt-0 lg:pl-12"
          >
            <h2
              id="profile-contact-heading"
              className="text-lg font-semibold tracking-tight"
            >
              {t("sections.contact")}
            </h2>
            <dl className="grid grid-cols-1 gap-x-6 gap-y-6 sm:grid-cols-2">
              <ProfileField
                label={t("fields.phone")}
                value={show(profile.phone)}
                className="sm:col-span-2"
              />
              <ProfileField
                label={t("fields.addressLine")}
                value={show(profile.addressLine)}
                className="sm:col-span-2"
              />
              <ProfileField
                label={t("fields.city")}
                value={show(profile.city)}
              />
              <ProfileField
                label={t("fields.state")}
                value={show(profile.state)}
              />
            </dl>
          </section>
        </div>
      </Card>
    </section>
  );
}
