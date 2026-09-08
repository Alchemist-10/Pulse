import { useId } from "react";
import type { ReactElement } from "react";
import { Label } from "./Label";

interface FormFieldProps {
  label: string;
  /** Field-level error message, already localized. */
  error?: string;
  hint?: string;
  /**
   * Render prop given the ids to wire onto the control:
   * `id`, plus `aria-describedby` / `aria-errormessage` when present.
   */
  children: (props: {
    id: string;
    "aria-describedby"?: string;
    "aria-errormessage"?: string;
    invalid: boolean;
  }) => ReactElement;
}

// Label + control + error, wired together for screen readers. One place, so the
// association is not re-derived (and re-broken) on every screen.
export function FormField({ label, error, hint, children }: FormFieldProps) {
  const id = useId();
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const describedBy =
    [hint ? hintId : null, error ? errorId : null].filter(Boolean).join(" ") ||
    undefined;

  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      {hint && (
        <p id={hintId} className="text-xs text-muted">
          {hint}
        </p>
      )}
      {children({
        id,
        "aria-describedby": describedBy,
        "aria-errormessage": error ? errorId : undefined,
        invalid: Boolean(error),
      })}
      {error && (
        <p id={errorId} className="text-xs font-medium text-critical">
          {error}
        </p>
      )}
    </div>
  );
}
