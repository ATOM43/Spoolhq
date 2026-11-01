import { useId, type ComponentProps } from "react";

import { Button } from "./button";

/**
 * A button that, when `reason` is set, is disabled and says why and what to do: as a
 * hover tooltip (on a wrapper, since disabled buttons get no pointer events) and as
 * the button's accessible description.
 */
export function ReasonButton({
  reason,
  disabled,
  ...props
}: ComponentProps<typeof Button> & { reason?: string | null | undefined }) {
  const id = useId();
  if (!reason) {
    return <Button disabled={disabled} {...props} />;
  }
  return (
    <span title={reason} className="inline-flex">
      <Button disabled aria-describedby={id} {...props} />
      <span id={id} className="sr-only">
        {reason}
      </span>
    </span>
  );
}
