import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

// Also exported as TextField for callers that prefer that name.
export function Input({ invalid, className, ...props }: InputProps) {
  return (
    <input
      aria-invalid={invalid || undefined}
      className={cn(
        "block w-full rounded-md border bg-surface px-3 py-2 text-sm text-foreground shadow-sm",
        "min-h-11 placeholder:text-muted outline-none transition-[box-shadow,border-color]",
        "focus-visible:ring-2 focus-visible:ring-focus-ring/40 focus-visible:border-focus-ring",
        "focus-visible:ring-offset-0",
        invalid ? "border-critical-border" : "border-border-strong",
        className,
      )}
      {...props}
    />
  );
}

export { Input as TextField };
