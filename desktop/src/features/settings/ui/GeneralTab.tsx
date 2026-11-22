import { CircleCheck, CircleX, LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";

import { quitApp } from "@/shared/api";
import { Button, CopyCommand } from "@/shared/ui";

import {
  useDaemonSettings,
  useSaveKeepRunning,
  useVersion,
} from "../model/queries";

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
 * D2 · General: "keep running", saved through the daemon to `~/.spoolhq/config.toml`,
 * and the folders, read-only (set in that file or `SPOOLHQ_*` variables). Theme and
 * notifications have nowhere to live yet, so they are not shown.
 */
export function GeneralTab() {
  const settings = useDaemonSettings();
  const save = useSaveKeepRunning();
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
      <div className="flex flex-col gap-1 text-sm">
        <label className="flex items-center gap-2 font-medium">
          <input
            type="checkbox"
            checked={
              save.isPending
                ? save.variables
                : settings.data.desktop.keep_running
            }
            disabled={save.isPending}
            onChange={(event) => {
              save.mutate(event.target.checked);
            }}
          />
          Keep running when the window is closed
        </label>
        <span className="text-xs text-ink-muted">
          Runs go on in the background; open SpoolHQ again from the tray icon,
          or by starting it again.
        </span>
        {save.isError ? (
          <p role="alert" className="text-danger">
            Couldn't save: {save.error.message}
          </p>
        ) : null}
      </div>
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
      <div className="flex flex-col items-start gap-1 text-sm">
        <Button
          variant="secondary"
          onClick={() => {
            void quitApp();
          }}
        >
          Quit SpoolHQ
        </Button>
        <span className="text-xs text-ink-muted">
          Also in the tray icon&apos;s menu. Stops the daemon SpoolHQ started,
          and asks first if a run is going.
        </span>
      </div>
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
