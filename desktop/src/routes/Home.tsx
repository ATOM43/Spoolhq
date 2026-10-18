import { CircleCheck, FolderOpen } from "lucide-react";

import {
  DaemonConnectingPanel,
  DaemonDownPanel,
  DaemonErrorPanel,
} from "@/components/DaemonPanel";
import { EmptyState } from "@/components/EmptyState";
import { SettingsDialog } from "@/components/SettingsDialog";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useDaemonStatus } from "@/daemon/useDaemonStatus";

export function Home() {
  const { status, checking, retry } = useDaemonStatus();

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Home</h1>
        <SettingsDialog />
      </div>

      {status.state === "ok" ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CircleCheck aria-hidden className="size-5 text-success" />
                Daemon ok · v{status.version}
              </CardTitle>
              <CardDescription>
                Connected to 127.0.0.1:{status.port}.
              </CardDescription>
            </CardHeader>
          </Card>
          <EmptyState
            icon={<FolderOpen aria-hidden />}
            title="No projects yet"
            description="Projects you create will be listed here."
          />
        </>
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
