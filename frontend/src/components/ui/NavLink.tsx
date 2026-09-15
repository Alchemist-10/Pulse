import type { ComponentProps } from "react";
import { ArrowLeftIcon, ArrowRightIcon } from "lucide-react";
import { Link } from "@/i18n/navigation";
import { cn } from "@/lib/cn";
import { buttonVariants } from "./Button";

interface NavLinkProps extends ComponentProps<typeof Link> {
  variant?: "ghost" | "soft" | "secondary";
  /** "back" prepends a left arrow, "forward" appends a right arrow. */
  icon?: "back" | "forward" | "none";
}

// The in-page navigation link (back-to-X, cross-links between screens) —
// P5 redesign replacement for the old underlined <Link>. Same shadcn-style
// button language as Button, rendered as a real link so it stays a link
// (correct semantics, middle-click, right-click-open-in-new-tab).
export function NavLink({
  variant = "ghost",
  icon = "none",
  className,
  children,
  ...props
}: NavLinkProps) {
  return (
    <Link
      className={cn(buttonVariants({ variant, size: "nav" }), className)}
      {...props}
    >
      {icon === "back" && <ArrowLeftIcon className="size-4" aria-hidden="true" />}
      {children}
      {icon === "forward" && <ArrowRightIcon className="size-4" aria-hidden="true" />}
    </Link>
  );
}
