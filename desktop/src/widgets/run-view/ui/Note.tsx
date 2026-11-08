import { LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";

/** A panel's one-line state: before its step, while it runs, or nothing to show. */
export function Note({
  children,
  busy = false,
}: {
  children: ReactNode;
  busy?: boolean;
}) {
  return (
    <p className="flex items-center gap-2 py-2 text-sm text-ink-muted">
      {busy ? (
        <LoaderCircle aria-hidden className="size-4 motion-safe:animate-spin" />
      ) : null}
      <span>{children}</span>
    </p>
  );
}
