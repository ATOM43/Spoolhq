import { CircleCheck, CircleX, LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";

import { CopyCommand } from "@/shared/ui";

import { useDaemonSettings, useVersion } from "../model/queries";

const REPOSITORY = "https://github.com/ATOM43/Spoolhq";

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1 text-sm">
      <span className="font-medium">{label}</span>
      {children}
    </div>
  );
}

/**
 * D2 · General: what the daemon stores today, read-only (it is set in
 * `~/.spoolhq/config.toml` or `SPOOLHQ_*` variables). Theme, notifications and
 * "keep running" have nowhere to live yet, so they are not shown.
 */
export function GeneralTab() {
  const settings = useDaemonSettings();
  if (settings.isPending) {
    return (
      <p className="flex items-center gap-2 text-sm text-ink-muted">
        <LoaderCircle aria-hidden className="size-4 animate-spin" />
        Loading settings…
      </p>
    );
  }
  if (settings.isError) {
    return (
      <p role="alert" className="text-sm text-danger">
        Couldn't load the settings: {settings.error.message}
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-4">
      <Row label="Projects folder">
        <CopyCommand command={settings.data.projects_dir} />
      </Row>
      <Row label="Worktrees folder">
        <CopyCommand command={settings.data.worktrees_dir} />
      </Row>
      <p className="text-xs text-ink-muted">
        Change these in ~/.spoolhq/config.toml (or SPOOLHQ_PROJECTS_DIR and
        SPOOLHQ_WORKTREES_DIR), then restart the daemon.
      </p>
    </div>
  );
}

/** D2 · About: version, daemon status and where the code lives. */
export function AboutTab() {
  const version = useVersion();
  const settings = useDaemonSettings();
  return (
    <div className="flex flex-col gap-4">
      <Row label="Version">
        <span className="font-mono">
          {version.data?.version ?? (version.isPending ? "…" : "unknown")}
        </span>
      </Row>
      <Row label="Daemon">
        {version.isSuccess ? (
          <span className="flex items-center gap-1.5 text-success">
            <CircleCheck aria-hidden className="size-4" />
            Running
            {settings.data
              ? ` on ${settings.data.host}:${String(settings.data.port)}`
              : ""}
          </span>
        ) : version.isError ? (
          <span className="flex items-center gap-1.5 text-danger">
            <CircleX aria-hidden className="size-4" />
            Not answering: {version.error.message}
          </span>
        ) : (
          <span className="text-ink-muted">Checking…</span>
        )}
      </Row>
      <Row label="Repository">
        <CopyCommand command={REPOSITORY} />
      </Row>
    </div>
  );
}
