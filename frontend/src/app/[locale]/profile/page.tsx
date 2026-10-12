"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import {
  CalendarDaysIcon,
  CopyIcon,
  InfoIcon,
  LanguagesIcon,
  MapPinIcon,
  PhoneIcon,
  UserRoundIcon,
  type LucideIcon,
} from "lucide-react";
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

import styles from "./profile.module.css";

const EMPTY = "—"; // em dash for a missing identity field

function copySelectedText(element: HTMLElement): boolean {
  const selection = window.getSelection();
  if (!selection) return false;

  const range = document.createRange();
  range.selectNodeContents(element);
  selection.removeAllRanges();
  selection.addRange(range);

  try {
    const copied = document.execCommand("copy");
    if (copied) selection.removeAllRanges();
    return copied;
  } catch {
    // Keep the ID selected so the patient can copy it manually.
    return false;
  }
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; profile: PatientProfile }
  | { status: "notFound" }
  | { status: "error"; message: string };

function ProfileSkeleton() {
  return (
    <Card aria-hidden="true" className={cn(styles.card, "gap-0 py-0")}>
      <div
        className={cn(
          styles.header,
          "flex flex-wrap items-center gap-4 border-b p-6 sm:gap-6 sm:p-8",
        )}
      >
        <Skeleton className="size-20 shrink-0 rounded-full sm:size-24" />
        <div className="min-w-0 flex-1 space-y-3">
          <Skeleton className="h-8 w-48 max-w-full" />
        </div>
        <div className="basis-full space-y-2 border-t pt-4 sm:basis-auto sm:border-0 sm:pt-0">
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
              "min-w-0 space-y-4",
              group === 1 &&
                "border-t pt-8 lg:border-t-0 lg:border-l lg:pt-0 lg:pl-12",
            )}
          >
            <Skeleton className="h-6 w-40" />
            <div
              className={cn(
                "grid grid-cols-1",
                group === 1 && "sm:grid-cols-2",
              )}
            >
              {Array.from({ length: count }).map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    "min-w-0 space-y-1.5 border-b py-4 first:pt-0 last:border-b-0 last:pb-0",
                    group === 1 && i < 2 && "sm:col-span-2",
                    group === 1 && i === 2 && "sm:border-b-0 sm:pb-0",
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
  icon: Icon,
}: {
  label: string;
  value: string;
  className?: string;
  icon?: LucideIcon;
}) {
  return (
    <div
      className={cn(
        "min-w-0 space-y-1.5 border-b py-4 first:pt-0 last:border-b-0 last:pb-0",
        className,
      )}
    >
      <dt className="flex items-center gap-2 text-sm leading-relaxed text-muted-foreground">
        {Icon && (
          <Icon
            aria-hidden="true"
            className="size-4 shrink-0 text-primary/80"
            strokeWidth={1.75}
          />
        )}
        {label}
      </dt>
      <dd
        className={cn(
          "text-base leading-relaxed font-medium text-foreground [overflow-wrap:anywhere]",
          Icon && "pl-6",
        )}
      >
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
  const patientIdRef = useRef<HTMLSpanElement>(null);
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

      <Card className={cn(styles.card, styles.arrive, "gap-0 py-0")}>
        <div
          className={cn(
            styles.header,
            "flex flex-wrap items-center gap-4 border-b p-6 sm:gap-6 sm:p-8",
          )}
        >
          <svg
            aria-hidden="true"
            className={styles.contours}
            viewBox="0 0 640 320"
            fill="none"
          >
            <path
              d="M88 320C88 188 234 206 234 92S398-16 466-60M152 350C152 222 296 232 296 118S448 12 530-36M216 380C216 258 358 256 358 144S498 40 594-12"
              stroke="currentColor"
              strokeWidth="1"
            />
          </svg>
          <div
            aria-hidden="true"
            className={cn(
              styles.avatar,
              "flex size-20 shrink-0 items-center justify-center rounded-full text-primary sm:size-24",
            )}
          >
            <UserRoundIcon className="size-10 sm:size-12" strokeWidth={1.5} />
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
          <dl className="flex min-w-0 basis-full flex-wrap items-center justify-between gap-2 border-t border-primary/10 pt-4 sm:block sm:basis-auto sm:space-y-2 sm:border-0 sm:pt-0 sm:text-right">
            <dt className="text-sm text-muted-foreground">
              {t("claimed.label")}
            </dt>
            <dd>
              <Badge
                variant="secondary"
                className="h-auto max-w-full border border-primary/15 bg-card/80 px-3 py-1.5 whitespace-normal text-sm leading-relaxed"
              >
                {profile.claimed ? t("claimed.true") : t("claimed.false")}
              </Badge>
            </dd>
          </dl>
        </div>

        <div className="space-y-3 border-b bg-muted/20 px-6 py-5 sm:px-8">
          <dl>
            <dt className="text-sm text-muted-foreground">
              {t("fields.patientId")}
            </dt>
            <dd className="mt-2 flex min-w-0 flex-wrap items-center gap-x-4 gap-y-3">
              <span
                ref={patientIdRef}
                className="min-w-0 break-all text-sm font-medium text-foreground tabular-nums"
              >
                {profile.id}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  let copied = false;
                  try {
                    if (navigator.clipboard?.writeText) {
                      await navigator.clipboard.writeText(profile.id);
                      copied = true;
                    }
                  } catch {
                    // Some embedded browsers deny the async Clipboard API.
                  }

                  if (!copied && patientIdRef.current) {
                    copied = copySelectedText(patientIdRef.current);
                  }

                  if (copied) {
                    toast.success(t("copiedId"));
                  } else {
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
            className="min-w-0 space-y-4"
          >
            <h2
              id="profile-personal-heading"
              className="text-lg font-semibold tracking-tight"
            >
              {t("sections.personal")}
            </h2>
            <dl>
              <ProfileField
                label={t("fields.dateOfBirth")}
                icon={CalendarDaysIcon}
                value={formatDate(profile.dateOfBirth) || EMPTY}
              />
              <ProfileField
                label={t("fields.sex")}
                icon={UserRoundIcon}
                value={show(profile.sex)}
              />
              <ProfileField
                label={t("fields.localePreference")}
                icon={LanguagesIcon}
                value={localeLabel}
              />
            </dl>
          </section>
          <section
            aria-labelledby="profile-contact-heading"
            className="min-w-0 space-y-4 border-t pt-8 lg:border-t-0 lg:border-l lg:pt-0 lg:pl-12"
          >
            <h2
              id="profile-contact-heading"
              className="text-lg font-semibold tracking-tight"
            >
              {t("sections.contact")}
            </h2>
            <dl className="grid grid-cols-1 sm:grid-cols-2">
              <ProfileField
                label={t("fields.phone")}
                icon={PhoneIcon}
                value={show(profile.phone)}
                className="sm:col-span-2"
              />
              <ProfileField
                label={t("fields.addressLine")}
                icon={MapPinIcon}
                value={show(profile.addressLine)}
                className="sm:col-span-2"
              />
              <ProfileField
                label={t("fields.city")}
                value={show(profile.city)}
                className="sm:border-b-0 sm:pb-0"
              />
              <ProfileField
                label={t("fields.state")}
                value={show(profile.state)}
                className="sm:pt-4"
              />
            </dl>
          </section>
        </div>
      </Card>
    </section>
  );
}
