import type { ButtonHTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";
import { SpinnerIcon } from "./icons";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium " +
    "min-h-11 px-4 py-2 transition-colors outline-none " +
    "focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 " +
    "focus-visible:ring-offset-background disabled:opacity-60 disabled:pointer-events-none",
  {
    variants: {
      variant: {
        primary: "bg-accent text-accent-contrast shadow-sm hover:bg-accent-hover",
        secondary:
          "bg-surface text-foreground border border-border-strong shadow-sm hover:bg-surface-raised",
        ghost: "bg-transparent text-accent-text hover:bg-accent-subtle",
      },
    },
    defaultVariants: {
      variant: "primary",
    },
  },
);

interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** Shows a spinner and disables the button. */
  loading?: boolean;
}

// Mobile-first: min-h-11 (44px) keeps the tap target usable on a mid-range
// Android. Wrapped once here so the same button is not rebuilt per screen.
export function Button({
  variant,
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
      className={cn(buttonVariants({ variant }), className)}
      {...props}
    >
      {loading && <SpinnerIcon className="size-4 animate-spin" />}
      {children}
    </button>
  );
}
