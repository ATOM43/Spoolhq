import { CircleAlert, CircleCheck, CircleX, LoaderCircle } from "lucide-react";

import type { DaemonStatus } from "@/daemon/status";
import { cn } from "@/lib/utils";

/** The daemon's state as icon + label (never colour alone). */
export function StatusPill({ status }: { status: DaemonStatus }) {
  const { icon, label, tone } = describe(status);
  return (
    <span
      role="status"
      aria-live="polite"
      className={cn(
        "inline-flex items-center gap-2 rounded-lg border bg-surface-sunken px-3 py-1 text-sm",
        tone,
      )}
    >
      {icon}
      <span className="text-ink">{label}</span>
    </span>
  );
}

function describe(status: DaemonStatus) {
  switch (status.state) {
    case "ok":
      return {
        icon: <CircleCheck aria-hidden className="size-4" />,
        label: `Daemon ok · v${status.version}`,
        tone: "text-success",
      };
    case "reconnecting":
      return {
        icon: <LoaderCircle aria-hidden className="size-4 animate-spin" />,
        label: "Reconnecting…",
        tone: "text-warning",
      };
    case "down":
      return {
        icon: <CircleX aria-hidden className="size-4" />,
        label: "Daemon not running",
        tone: "text-danger",
      };
    case "error":
      return {
        icon: <CircleAlert aria-hidden className="size-4" />,
        label: "Daemon error",
        tone: "text-danger",
      };
  }
}
