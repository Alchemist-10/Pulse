import type { ComponentPropsWithoutRef } from "react";
import { Label as RadixLabel } from "radix-ui";
import { cn } from "@/lib/cn";

type LabelProps = ComponentPropsWithoutRef<typeof RadixLabel.Root>;

export function Label({ className, ...props }: LabelProps) {
  return (
    <RadixLabel.Root
      className={cn("block text-sm font-medium text-foreground", className)}
      {...props}
    />
  );
}
