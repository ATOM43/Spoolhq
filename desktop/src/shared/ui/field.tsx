import type { ReactNode } from "react";

import { describedBy } from "./field-ids";

/**
 * A labelled form control with its hint or error underneath. Give the control
 * `id={id}`, `aria-describedby={describedBy(id)}` and `aria-invalid={!!error}`.
 */
export function Field({
  id,
  label,
  hint,
  error,
  children,
}: {
  id: string;
  label: string;
  hint?: string | undefined;
  error?: string | null;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium">
        {label}
      </label>
      {children}
      {error ? (
        <p id={describedBy(id)} role="alert" className="text-sm text-danger">
          {error}
        </p>
      ) : hint ? (
        <p id={describedBy(id)} className="text-sm text-ink-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
