"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { ArrowRightIcon, BellIcon, CheckIcon, XIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverClose,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Skeleton } from "@/components/ui/skeleton";
import { Link, usePathname } from "@/i18n/navigation";
import { api, ApiError } from "@/lib/api";
import { useApiErrorMessage } from "@/lib/errors";
import { formatDateTime } from "@/lib/format";
import {
  NOTIFICATIONS_CHANGED_EVENT,
  type Notification,
} from "@/lib/notifications";
import type { Page } from "@/lib/records";

type PreviewState =
  | { status: "loading" }
  | { status: "error"; error: unknown }
  | { status: "ready"; items: Notification[] };

// The preview is scoped to the signed-in Patient (keyed by User in AppHeader).
// A dot means unread activity among these five recent items, never a total.
export function NotificationBell() {
  const t = useTranslations("notifications");
  const locale = useLocale();
  const pathname = usePathname();
  const errorMessage = useApiErrorMessage();
  const titleId = useId();
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<PreviewState>({ status: "loading" });
  const request = useRef<AbortController | null>(null);

  const refresh = useCallback(async () => {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setState({ status: "loading" });
    try {
      const page = await api.get<Page<Notification>>("/notifications?limit=5", {
        signal: controller.signal,
      });
      if (!controller.signal.aborted)
        setState({ status: "ready", items: page.items });
    } catch (error) {
      if (controller.signal.aborted) return;
      if (
        error instanceof ApiError &&
        (error.status === 401 || error.code === "SESSION_EXPIRED")
      ) {
        setState({ status: "ready", items: [] });
        setOpen(false);
        return;
      }
      setState({ status: "error", error });
    }
  }, []);

  useEffect(() => {
    // Defer state changes until the effect setup has completed.
    let active = true;
    void Promise.resolve().then(() => {
      if (!active) return;
      setOpen(false);
      void refresh();
    });
    const onRefresh = () => {
      if (document.visibilityState === "visible") void refresh();
    };
    window.addEventListener("focus", onRefresh);
    document.addEventListener("visibilitychange", onRefresh);
    window.addEventListener(NOTIFICATIONS_CHANGED_EVENT, onRefresh);
    return () => {
      active = false;
      request.current?.abort();
      window.removeEventListener("focus", onRefresh);
      document.removeEventListener("visibilitychange", onRefresh);
      window.removeEventListener(NOTIFICATIONS_CHANGED_EVENT, onRefresh);
    };
  }, [pathname, refresh]);

  const unread =
    state.status === "ready" && state.items.some((item) => !item.readAt);

  return (
    <Popover
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (next) void refresh();
      }}
    >
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative size-11"
          aria-label={unread ? t("preview.unreadLabel") : t("title")}
        >
          <BellIcon aria-hidden="true" className="size-[18px]" />
          {unread && (
            <span
              aria-hidden="true"
              className="absolute top-2 right-2 size-2 rounded-full bg-primary ring-2 ring-card"
            />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent aria-labelledby={titleId}>
        <div className="flex items-center justify-between gap-3 border-b px-5 py-3">
          <div className="min-w-0">
            <h2 id={titleId} className="text-base font-semibold">
              {t("title")}
            </h2>
            <p className="text-xs text-muted-foreground">
              {t("preview.recent")}
            </p>
          </div>
          <PopoverClose asChild>
            <Button
              variant="ghost"
              size="icon"
              className="size-11"
              aria-label={t("preview.close")}
            >
              <XIcon aria-hidden="true" />
            </Button>
          </PopoverClose>
        </div>
        <div aria-live="polite" aria-busy={state.status === "loading"}>
          {state.status === "loading" && (
            <div className="space-y-4 p-5">
              <span className="sr-only">{t("loading")}</span>
              {Array.from({ length: 3 }, (_, index) => (
                <div key={index} aria-hidden="true" className="space-y-2">
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-1/3" />
                </div>
              ))}
            </div>
          )}
          {state.status === "error" && (
            <div className="space-y-3 p-5">
              <p className="text-sm font-medium">{t("error.title")}</p>
              <p className="text-sm text-muted-foreground">
                {errorMessage(state.error)}
              </p>
              <Button variant="outline" onClick={() => void refresh()}>
                {t("error.retry")}
              </Button>
            </div>
          )}
          {state.status === "ready" && state.items.length === 0 && (
            <div className="px-6 py-8 text-center">
              <BellIcon
                aria-hidden="true"
                className="mx-auto mb-3 size-6 text-muted-foreground"
              />
              <p className="text-sm font-medium">{t("empty.title")}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {t("empty.body")}
              </p>
            </div>
          )}
          {state.status === "ready" && state.items.length > 0 && (
            <ul className="divide-y">
              {state.items.map((item) => (
                <li key={item.id} className="space-y-1.5 px-5 py-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <p className="min-w-0 text-sm font-medium">
                      {t(`list.types.${item.type}`)}
                    </p>
                    <span
                      className={
                        item.readAt
                          ? "flex items-center gap-1 text-xs text-muted-foreground"
                          : "flex items-center gap-1 text-xs font-medium text-primary"
                      }
                    >
                      {item.readAt ? (
                        <CheckIcon aria-hidden="true" className="size-3" />
                      ) : (
                        <span
                          aria-hidden="true"
                          className="size-1.5 rounded-full bg-primary"
                        />
                      )}
                      {t(item.readAt ? "list.read" : "list.unread")}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {item.type === "DAILY_DIGEST"
                      ? t("content.DAILY_DIGEST", {
                          count:
                            typeof item.params?.viewCount === "number"
                              ? item.params.viewCount
                              : 0,
                        })
                      : t(`content.${item.type}`)}
                  </p>
                  <time
                    dateTime={item.createdAt}
                    className="block text-xs tabular-nums text-muted-foreground"
                  >
                    {formatDateTime(item.createdAt, `${locale}-IN`)}
                  </time>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="border-t px-3 py-2">
          <Button
            asChild
            variant="ghost"
            className="h-auto min-h-11 w-full justify-between whitespace-normal text-left text-primary"
          >
            <Link href="/notifications" onClick={() => setOpen(false)}>
              {t("preview.viewAll")}
              <ArrowRightIcon aria-hidden="true" />
            </Link>
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
