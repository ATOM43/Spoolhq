import { CircleArrowUp, LoaderCircle, RefreshCw } from "lucide-react";

import { useProjects } from "@/entities/project";
import {
  useCheckNow,
  useInstallUpdate,
  useUpdateStatus,
} from "@/entities/update";
import type { UpdateStatus } from "@/shared/api";
import { formatTime, timeAgo } from "@/shared/lib";
import { Button, ReasonButton } from "@/shared/ui";

/** "Wait for the run to finish (T05)" while any project has a run going or paused. */
function useRunBlocker(): string | null {
  const projects = useProjects().data ?? [];
  const running = projects
    .filter((p) => p.run_state === "running" || p.run_state === "paused")
    .map((p) => p.run?.ticket_id ?? p.name);
  if (running.length === 0) {
    return null;
  }
  return running.length === 1
    ? `Wait for the run to finish (${running[0] ?? ""})`
    : `Wait for the runs to finish (${running.join(", ")})`;
}

function When({ ms }: { ms: number }) {
  const iso = new Date(ms).toISOString();
  return <time title={formatTime(iso)}>{timeAgo(iso)}</time>;
}

function CheckNow() {
  const check = useCheckNow();
  return (
    <Button
      variant="secondary"
      size="sm"
      disabled={check.isPending}
      onClick={() => {
        check.mutate();
      }}
    >
      {check.isPending ? (
        <LoaderCircle aria-hidden className="animate-spin" />
      ) : (
        <RefreshCw aria-hidden />
      )}
      Check now
    </Button>
  );
}

function Install({ status }: { status: UpdateStatus }) {
  const install = useInstallUpdate();
  const blocker = useRunBlocker();
  if (status.install === "package") {
    return (
      <p className="text-sm">Download the new package from the release page</p>
    );
  }
  const busy = install.isPending || status.installing;
  return (
    <div className="flex flex-col items-start gap-1 text-sm">
      <ReasonButton
        reason={blocker}
        disabled={busy}
        onClick={() => {
          install.mutate();
        }}
      >
        {busy ? <LoaderCircle aria-hidden className="animate-spin" /> : null}
        Install and restart
      </ReasonButton>
      {blocker ? (
        <span className="text-xs text-ink-muted">{blocker}</span>
      ) : null}
      {status.external_daemon ? (
        <span className="text-xs text-ink-muted">
          Your own daemon keeps running; restart it to update it.
        </span>
      ) : null}
      {status.install_error ? (
        <p role="alert" className="text-danger">
          {status.install_error}
        </p>
      ) : null}
    </div>
  );
}

/** About's update state: up to date, a quiet failure, or the new version to install. */
export function UpdateSection() {
  const status = useUpdateStatus().data;
  if (!status) {
    return null;
  }
  const { check } = status;
  switch (check.state) {
    case "available":
      return (
        <div className="flex flex-col gap-2 text-sm">
          <span className="flex items-center gap-1.5 font-medium">
            <CircleArrowUp aria-hidden className="size-4 text-accent" />
            Update available · v{status.current_version} → v{check.version}
          </span>
          {check.notes ? (
            // Plain text only: the feed's notes are never rendered as HTML or links.
            <pre
              aria-label="Release notes"
              className="max-h-40 overflow-auto rounded-md border bg-surface-sunken p-2 font-sans text-xs whitespace-pre-wrap"
            >
              {check.notes}
            </pre>
          ) : null}
          <Install status={status} />
        </div>
      );
    case "up_to_date":
      return (
        <div className="flex items-center gap-3 text-sm">
          <span>
            SpoolHQ is up to date · checked <When ms={check.checked_at} />
          </span>
          <CheckNow />
        </div>
      );
    case "failed":
      return (
        <div className="flex items-center gap-3 text-sm">
          <span className="text-ink-muted">
            Couldn't check for updates · <When ms={check.checked_at} />
          </span>
          <CheckNow />
        </div>
      );
    case "off":
      return (
        <span className="text-sm text-ink-muted">
          Update checks are off (General).
        </span>
      );
    case "unchecked":
      return (
        <div className="flex items-center gap-3 text-sm">
          <span className="text-ink-muted">Not checked yet</span>
          <CheckNow />
        </div>
      );
  }
}
