import { Plus } from "lucide-react";
import { Link } from "react-router";

import { useAgents } from "@/entities/agent";
import { useDaemonStatus } from "@/features/daemon-status";
import { NewProjectButton } from "@/features/project-create";
import { SettingsDialog } from "@/features/settings";
import { ReasonButton } from "@/shared/ui";

import { StatusPill } from "./StatusPill";

/** Amber "Fake runner" while the daemon replays a dev scenario (SPOOLHQ_DEV_FAKE_RUNNER). */
function FakeRunnerChip() {
  const scenario = useAgents().data?.fake_runner;
  if (!scenario) {
    return null;
  }
  return (
    <span
      title={scenario}
      className="rounded-full border border-warning/40 bg-warning/10 px-2 py-0.5 text-xs font-medium text-warning"
    >
      Fake runner
    </span>
  );
}

/** Home's top bar: app name, daemon status, Settings and + New project. */
export function TopBar() {
  const { status } = useDaemonStatus();
  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-4 border-b bg-surface-sunken px-6">
      <Link to="/" className="font-semibold tracking-tight">
        SpoolHQ
      </Link>
      <div className="flex items-center gap-3">
        {status.state === "ok" ? <FakeRunnerChip /> : null}
        <StatusPill status={status} />
        <SettingsDialog firstRun />
        {status.state === "ok" ? (
          <NewProjectButton />
        ) : (
          <ReasonButton reason="Waiting for the daemon">
            <Plus aria-hidden />
            New project
          </ReasonButton>
        )}
      </div>
    </header>
  );
}
