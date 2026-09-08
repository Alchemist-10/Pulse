"use client";

import { Select as RadixSelect } from "radix-ui";
import { cn } from "@/lib/cn";
import { CheckCircleIcon, ChevronDownIcon } from "./icons";

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  id?: string;
  value?: string;
  onValueChange: (value: string) => void;
  options: SelectOption[];
  placeholder: string;
  invalid?: boolean;
  "aria-describedby"?: string;
  "aria-errormessage"?: string;
}

// Wrapped Radix Select. Used for the Role picker on registration; wrapped once
// so the trigger/content styling is defined in a single place.
export function Select({
  id,
  value,
  onValueChange,
  options,
  placeholder,
  invalid,
  ...aria
}: SelectProps) {
  return (
    <RadixSelect.Root value={value} onValueChange={onValueChange}>
      <RadixSelect.Trigger
        id={id}
        aria-invalid={invalid || undefined}
        {...aria}
        className={cn(
          "inline-flex w-full items-center justify-between rounded-md border bg-surface",
          "min-h-11 px-3 py-2 text-sm text-foreground outline-none",
          "focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-1",
          "focus-visible:ring-offset-background data-[placeholder]:text-muted",
          invalid ? "border-critical-border" : "border-border-strong",
        )}
      >
        <RadixSelect.Value placeholder={placeholder} />
        <RadixSelect.Icon>
          <ChevronDownIcon className="size-4 text-muted" />
        </RadixSelect.Icon>
      </RadixSelect.Trigger>

      <RadixSelect.Portal>
        <RadixSelect.Content
          position="popper"
          sideOffset={4}
          className={cn(
            "z-50 min-w-(--radix-select-trigger-width) overflow-hidden rounded-md",
            "border border-border bg-surface-raised shadow-md",
          )}
        >
          <RadixSelect.Viewport className="p-1">
            {options.map((option) => (
              <RadixSelect.Item
                key={option.value}
                value={option.value}
                className={cn(
                  "flex cursor-pointer items-center justify-between rounded-sm px-2 py-2",
                  "text-sm text-foreground outline-none select-none",
                  "data-[highlighted]:bg-accent-subtle data-[highlighted]:text-accent-text",
                )}
              >
                <RadixSelect.ItemText>{option.label}</RadixSelect.ItemText>
                <RadixSelect.ItemIndicator>
                  <CheckCircleIcon className="size-4 text-accent-text" />
                </RadixSelect.ItemIndicator>
              </RadixSelect.Item>
            ))}
          </RadixSelect.Viewport>
        </RadixSelect.Content>
      </RadixSelect.Portal>
    </RadixSelect.Root>
  );
}
