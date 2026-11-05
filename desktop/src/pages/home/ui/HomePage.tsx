import { useDaemonStatus } from "@/features/daemon-status";
import {
  DaemonConnectingPanel,
  DaemonDownPanel,
  DaemonErrorPanel,
} from "@/widgets/daemon-down-panel";
import { TopBar } from "@/widgets/top-bar";

import { ProjectsSection } from "./ProjectsSection";

export function HomePage() {
  const { status, checking, retry } = useDaemonStatus();

  return (
    <div className="flex min-h-full flex-col">
      <TopBar />
      {status.state === "ok" ? (
        <div className="flex flex-col gap-8 px-6 py-8">
          <h1 className="text-2xl font-semibold tracking-tight">Home</h1>
          {/* Mounted only while the daemon answers, so its queries refetch when it is back. */}
          <ProjectsSection />
        </div>
      ) : (
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-6 py-16">
          {status.state === "down" ? (
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
      )}
    </div>
  );
}
