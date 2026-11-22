import { CircleAlert, CircleX, LoaderCircle, RotateCw } from "lucide-react";
import type { ReactNode } from "react";

import type { DaemonStatus } from "@/entities/daemon";
import type { DaemonError } from "@/shared/api";
import { DAEMON_HOST, DAEMON_START_COMMAND } from "@/shared/config";
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CopyCommand,
} from "@/shared/ui";

interface RetryProps {
  onRetry: () => void;
  checking: boolean;
}

/** The panel for any status but "ok": Home and the project page show it instead. */
export function DaemonStatusPanel({
  status,
  onRetry,
  checking,
}: RetryProps & { status: Exclude<DaemonStatus, { state: "ok" }> }) {
  switch (status.state) {
    case "down":
      return (
        <DaemonDownPanel
          port={status.port}
          logDir={status.logDir}
          onRetry={onRetry}
          checking={checking}
        />
      );
    case "error":
      return (
        <DaemonErrorPanel
          error={status.error}
          onRetry={onRetry}
          checking={checking}
        />
      );
    case "port_in_use":
      return (
        <PortInUsePanel
          port={status.port}
          configPath={status.configPath}
          onRetry={onRetry}
          checking={checking}
        />
      );
    case "starting":
      return <BusyPanel title="Starting SpoolHQ…" />;
    case "reconnecting":
      return <BusyPanel title="Looking for the daemon…" />;
  }
}

/** Shown on Home when nothing answers on the daemon's port. `logDir` is set when the
 * app started its own daemon and it did not answer. */
export function DaemonDownPanel({
  port,
  logDir = null,
  onRetry,
  checking,
}: RetryProps & { port: number | null; logDir?: string | null }) {
  const where = port === null ? "" : ` on ${DAEMON_HOST}:${String(port)}`;
  const started =
    logDir === null
      ? ""
      : ` The app started its daemon, but it did not answer; its logs are in ${logDir}.`;
  return (
    <PanelCard
      icon={<CircleX aria-hidden className="size-5 text-danger" />}
      title="The daemon isn't running"
      description={`SpoolHQ needs its daemon${where}.${started} Your projects appear here once it is running; the app checks again every 3 seconds.`}
      onRetry={onRetry}
      checking={checking}
    >
      <CopyCommand command={DAEMON_START_COMMAND} />
    </PanelCard>
  );
}

/** Shown on Home when the daemon answers but cannot be used. */
export function DaemonErrorPanel({
  error,
  onRetry,
  checking,
}: RetryProps & { error: DaemonError }) {
  const { title, description, command } = explain(error);
  return (
    <PanelCard
      icon={<CircleAlert aria-hidden className="size-5 text-danger" />}
      title={title}
      description={description}
      onRetry={onRetry}
      checking={checking}
    >
      {command === undefined ? null : <CopyCommand command={command} />}
    </PanelCard>
  );
}

/** Shown when another program answers on the daemon's port, so the app started none. */
export function PortInUsePanel({
  port,
  configPath,
  onRetry,
  checking,
}: RetryProps & { port: number; configPath: string }) {
  return (
    <PanelCard
      icon={<CircleAlert aria-hidden className="size-5 text-danger" />}
      title={`Port ${String(port)} is used by another program`}
      description={`SpoolHQ did not start its daemon because another program answers on ${DAEMON_HOST}:${String(port)}. Stop that program, or pick a free port: set port = ${String(port + 1)} in ${configPath} (or the SPOOLHQ_PORT environment variable), then restart SpoolHQ.`}
      onRetry={onRetry}
      checking={checking}
    >
      {null}
    </PanelCard>
  );
}

/** Shown while the first check is in flight or the app's own daemon is starting, so
 * the window is never blank. */
function BusyPanel({ title }: { title: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <LoaderCircle aria-hidden className="size-5 animate-spin" />
          {title}
        </CardTitle>
      </CardHeader>
    </Card>
  );
}

/** V1 · Daemon not running: a red alert with Retry, then the command to start it. */
function PanelCard({
  icon,
  title,
  description,
  onRetry,
  checking,
  children,
}: RetryProps & {
  icon: ReactNode;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <>
      <div className="flex items-start gap-3 rounded-lg bg-danger/10 px-4 py-3">
        <span className="mt-0.5 shrink-0">{icon}</span>
        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
          <h2 className="font-semibold">{title}</h2>
          <p className="text-sm text-ink-muted">{description}</p>
        </div>
        <Button onClick={onRetry} disabled={checking} className="shrink-0">
          <RotateCw
            aria-hidden
            className={checking ? "animate-spin" : undefined}
          />
          Retry
        </Button>
      </div>
      {children === null ? null : (
        <Card>
          <CardContent className="flex flex-col gap-3">
            <p className="text-sm text-ink-muted">
              Or start it yourself in a terminal, then press Retry:
            </p>
            {children}
          </CardContent>
        </Card>
      )}
    </>
  );
}

function explain(error: DaemonError): {
  title: string;
  description: string;
  command?: string;
} {
  const { detail } = error;
  switch (detail.kind) {
    case "token_missing":
      return {
        title: "The daemon's access token is missing",
        description: `SpoolHQ reads the token from ${detail.tokenPath}, and that file does not exist. The daemon creates it when it starts; restart it to write the file.`,
        command: DAEMON_START_COMMAND,
      };
    case "unauthorized":
      return {
        title: "The daemon rejected the access token",
        description:
          "The token file does not match the running daemon. Restart the daemon so both use the same token.",
        command: DAEMON_START_COMMAND,
      };
    case "bad_host":
      return {
        title: "The daemon refused the connection",
        description:
          "It rejected the request's Host header. Check that nothing else is listening on the daemon's port.",
      };
    case "config":
      return {
        title: "SpoolHQ's settings are invalid",
        description: detail.message,
      };
    case "not_running":
    case "api":
    case "http":
    case "invalid_response":
    case "internal":
      return {
        title: "Something went wrong talking to the daemon",
        description: error.message,
      };
  }
}
