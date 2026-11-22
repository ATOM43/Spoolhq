import { useQuery } from "@tanstack/react-query";
import {
  CloudAlert,
  CloudCheck,
  CloudUpload,
  LoaderCircle,
  RotateCcw,
} from "lucide-react";
import { useId } from "react";

import {
  trackerLabel,
  trackerQuery,
  useTrackerAction,
} from "@/entities/tracker";
import { formatTime, timeAgo } from "@/shared/lib";
import { Button, ReasonButton } from "@/shared/ui";

/** The header's sync line, shown only when the project has a tracker: its state as
 * icon + label, the error of a failed sync in a CSS-only tooltip with Retry, and Push
 * now (disabled while syncing). The error is rendered as text, never as HTML. */
export function TrackerLine({ project }: { project: string }) {
  const { data } = useQuery(trackerQuery(project));
  const action = useTrackerAction(project);
  const tipId = useId();
  if (!data?.kind) {
    return null;
  }
  const label = trackerLabel(data.kind);
  const busy = action.isPending;

  return (
    <span className="flex items-center gap-2 text-ink-muted">
      {data.state === "failed" ? (
        <span
          tabIndex={0}
          aria-describedby={tipId}
          className="group relative flex items-center gap-1 rounded-md text-danger outline-none focus-visible:ring-[3px] focus-visible:ring-accent/50"
        >
          <CloudAlert aria-hidden className="size-4" />
          {label} · sync failed
          <span
            id={tipId}
            role="tooltip"
            className="pointer-events-none absolute top-full left-0 z-50 mt-1 hidden max-w-sm rounded-md bg-ink px-2 py-1 text-xs font-medium text-surface group-hover:block group-focus-visible:block"
          >
            {data.last_error}
          </span>
        </span>
      ) : data.state === "syncing" ? (
        <span className="flex items-center gap-1">
          <LoaderCircle aria-hidden className="size-4 animate-spin" />
          {label} · syncing · {data.pending} pending
        </span>
      ) : (
        <span className="flex items-center gap-1">
          <CloudCheck aria-hidden className="size-4" />
          {label} ·{" "}
          {data.last_synced_at ? (
            <time
              dateTime={data.last_synced_at}
              title={formatTime(data.last_synced_at)}
            >
              synced {timeAgo(data.last_synced_at)}
            </time>
          ) : (
            "up to date"
          )}
        </span>
      )}
      {data.state === "failed" ? (
        <Button
          size="sm"
          variant="outline"
          disabled={busy}
          onClick={() => {
            action.mutate("retry");
          }}
        >
          <RotateCcw aria-hidden />
          Retry
        </Button>
      ) : null}
      <ReasonButton
        size="sm"
        variant="ghost"
        disabled={busy}
        reason={
          data.state === "syncing"
            ? `Syncing ${String(data.pending)} change(s); push again once it's done`
            : null
        }
        onClick={() => {
          action.mutate("push");
        }}
      >
        <CloudUpload aria-hidden />
        Push now
      </ReasonButton>
      {action.error ? (
        <span role="alert" className="text-danger">
          {action.error.message}
        </span>
      ) : null}
    </span>
  );
}
