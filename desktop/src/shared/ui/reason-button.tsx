import { useId, type ComponentProps } from "react";

import { cn } from "@/shared/lib";

import { Button } from "./button";

/**
 * A button that, when `reason` is set, is disabled, looks it (muted, never the accent)
 * and says why and what to do: in a tooltip shown on hover and on keyboard focus (on a
 * focusable wrapper, since a disabled button gets neither), as the button's accessible
 * description, and as a `title` fallback. CSS classes only: the CSP blocks inline styles.
 */
export function ReasonButton({
  reason,
  disabled,
  className,
  ...props
}: ComponentProps<typeof Button> & { reason?: string | null | undefined }) {
  const id = useId();
  if (!reason) {
    return <Button disabled={disabled} className={className} {...props} />;
  }
  return (
    <span
      title={reason}
      // Focusable so keyboard users reach the reason; the button itself can't take focus.
      tabIndex={0}
      aria-describedby={id}
      className="group relative inline-flex rounded-md outline-none focus-visible:ring-[3px] focus-visible:ring-accent/50"
    >
      <Button
        {...props}
        variant="outline"
        disabled
        aria-describedby={id}
        className={cn(
          className,
          "bg-surface-sunken text-ink-muted disabled:opacity-100",
        )}
      />
      <span
        id={id}
        role="tooltip"
        className="pointer-events-none absolute top-full right-0 z-50 mt-1 hidden rounded-md bg-ink px-2 py-1 text-xs font-medium whitespace-nowrap text-surface group-hover:block group-focus-visible:block"
      >
        {reason}
      </span>
    </span>
  );
}
