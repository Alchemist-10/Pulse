import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import { AlertTriangleIcon, CheckCircleIcon, InfoIcon } from "./icons";

type Tone = "error" | "success" | "info";

interface CalloutProps {
  tone?: Tone;
  /** Accessible label for the leading icon, e.g. "Error". */
  iconLabel: string;
  children: ReactNode;
}

const tones: Record<Tone, { wrap: string; icon: typeof InfoIcon }> = {
  // Colour is never the only signal: each tone pairs a hue with an icon and the
  // caller-supplied iconLabel text (.claude/rules/frontend.md).
  error: {
    wrap: "bg-critical-surface text-critical border-critical-border",
    icon: AlertTriangleIcon,
  },
  success: {
    wrap: "bg-consent-active-surface text-consent-active border-consent-active",
    icon: CheckCircleIcon,
  },
  info: {
    wrap: "bg-audit-normal-surface text-audit-normal border-border-strong",
    icon: InfoIcon,
  },
};

// Form-error and status banner. `role="alert"` so a submit failure is announced.
export function Callout({ tone = "info", iconLabel, children }: CalloutProps) {
  const { wrap, icon: Icon } = tones[tone];
  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-2 rounded-md border border-l-4 px-3 py-2 text-sm",
        wrap,
      )}
    >
      <Icon className="mt-0.5 size-5 shrink-0" />
      <span>
        <span className="sr-only">{iconLabel}: </span>
        {children}
      </span>
    </div>
  );
}
