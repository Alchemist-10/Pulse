import type { ButtonHTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";
import { SpinnerIcon } from "./icons";

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-semibold " +
    "transition-all outline-none no-underline " +
    "focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 " +
    "focus-visible:ring-offset-background disabled:opacity-60 disabled:pointer-events-none",
  {
    variants: {
      variant: {
        // AA note: both gradient stops pass 4.5:1 under white text, so the
        // hover overlay is what darkens — the base never lightens (see
        // --gradient-accent in tokens.css).
        primary:
          "bg-gradient-accent text-accent-contrast shadow-sm hover:shadow-md " +
          "hover:brightness-[1.06] active:brightness-[0.98]",
        secondary:
          "bg-surface text-foreground border border-border-strong shadow-sm hover:bg-surface-raised hover:shadow",
        // Soft accent fill — quiet CTAs on cards, quick-login, filter chips.
        soft: "bg-accent-soft text-accent-text hover:bg-accent-subtle",
        ghost: "bg-transparent text-accent-text hover:bg-accent-subtle",
      },
      // Mobile-first: min-h-11 (44px) keeps the tap target usable on a
      // mid-range Android — the default. "nav" is for inline text-link-style
      // navigation (back links, cross-links) where a 44px block would look
      // like chrome, not a sentence; it keeps a 44px *hit area* via negative
      // margin instead of visible height.
      size: {
        default: "min-h-11 px-4 py-2",
        nav: "-mx-2 -my-2 min-h-9 px-2 py-2 font-medium",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  },
);

interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** Shows a spinner and disables the button. */
  loading?: boolean;
}

// Wrapped once here so the same button is not rebuilt per screen.
export function Button({
  variant,
  size,
  loading = false,
  disabled,
  className,
  children,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    >
      {loading && <SpinnerIcon className="size-4 animate-spin" />}
      {children}
    </button>
  );
}
