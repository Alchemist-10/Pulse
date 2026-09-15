import type { ComponentProps } from "react";
import { Link } from "@/i18n/navigation";
import { cn } from "@/lib/cn";

// A link that sits inside a sentence ("Already have an account? Log in").
// P5 redesign replacement for the old permanently-underlined <Link> — the
// underline is now a hover/focus affordance, not a static line, matching
// how the rest of the redesign treats text links. Reach for NavLink instead
// when the link is a standalone action (a back link, a header button).
export function InlineLink({ className, ...props }: ComponentProps<typeof Link>) {
  return (
    <Link
      className={cn(
        "rounded-sm font-medium text-accent-text underline-offset-4 outline-none " +
          "hover:underline focus-visible:underline focus-visible:ring-2 focus-visible:ring-focus-ring",
        className,
      )}
      {...props}
    />
  );
}
