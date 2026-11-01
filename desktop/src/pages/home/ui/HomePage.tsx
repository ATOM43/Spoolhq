import { useDaemonStatus } from "@/features/daemon-status";
import { SettingsDialog } from "@/features/open-settings";
import { NewProjectButton } from "@/features/project-create";
import {
  DaemonConnectingPanel,
  DaemonDownPanel,
  DaemonErrorPanel,
} from "@/widgets/daemon-down-panel";

import { ProjectsSection } from "./ProjectsSection";

export function HomePage() {
  const { status, checking, retry } = useDaemonStatus();

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-8">
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold tracking-tight">Home</h1>
        <div className="flex items-center gap-2">
          <SettingsDialog />
          {status.state === "ok" ? <NewProjectButton /> : null}
        </div>
      </div>

      {status.state === "ok" ? (
        // Mounted only while the daemon answers, so its queries refetch when it is back.
        <ProjectsSection />
      ) : status.state === "down" ? (
        <DaemonDownPanel
          port={status.port}
          onRetry={retry}
          checking={checking}
        />
      ) : status.state === "error" ? (
        <DaemonErrorPanel
          error={status.error}
          onRetry={retry}
          checking={checking}
        />
      ) : (
        <DaemonConnectingPanel />
      )}
    </div>
  );
}
