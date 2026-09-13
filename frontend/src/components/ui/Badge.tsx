import type { HTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";

// Generic pill badge. Existing status chips (consent status, critical flag,
// unread notification) already pair colour with an icon and label inline —
// this only standardises the pill shape/typography, callers still supply
// their own colour classes via `className` where a fixed tone doesn't fit.
const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default: "border-transparent bg-accent-subtle text-accent-text",
        outline: "border-border-strong bg-surface text-foreground",
        critical: "border-critical-border bg-critical-surface text-critical",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

interface BadgeProps extends HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ variant, className, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
