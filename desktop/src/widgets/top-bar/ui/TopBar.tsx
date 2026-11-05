import { Plus } from "lucide-react";
import { Link } from "react-router";

import { useDaemonStatus } from "@/features/daemon-status";
import { NewProjectButton } from "@/features/project-create";
import { SettingsDialog } from "@/features/settings";
import { ReasonButton } from "@/shared/ui";

import { StatusPill } from "./StatusPill";

/** Home's top bar: app name, daemon status, Settings and + New project. */
export function TopBar() {
  const { status } = useDaemonStatus();
  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-4 border-b bg-surface-sunken px-6">
      <Link to="/" className="font-semibold tracking-tight">
        SpoolHQ
      </Link>
      <div className="flex items-center gap-3">
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
