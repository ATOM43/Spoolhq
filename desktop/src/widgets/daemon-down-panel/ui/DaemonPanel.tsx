import { CircleAlert, CircleX, LoaderCircle, RotateCw } from "lucide-react";
import type { ReactNode } from "react";

import type { DaemonError } from "@/shared/api";
import { DAEMON_HOST, DAEMON_START_COMMAND } from "@/shared/config";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  CopyCommand,
} from "@/shared/ui";

interface RetryProps {
  onRetry: () => void;
  checking: boolean;
}

/** Shown on Home when nothing answers on the daemon's port. */
export function DaemonDownPanel({
  port,
  onRetry,
  checking,
}: RetryProps & { port: number | null }) {
  const where = port === null ? "" : ` on ${DAEMON_HOST}:${String(port)}`;
  return (
    <PanelCard
      icon={<CircleX aria-hidden className="size-5 text-danger" />}
      title="The daemon isn't running"
      description={`SpoolHQ needs its daemon${where}. Start it in a terminal, then retry. The app also checks again every 3 seconds.`}
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

/** Shown on Home while the first check is in flight, so the window is never blank. */
export function DaemonConnectingPanel() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <LoaderCircle aria-hidden className="size-5 animate-spin" />
          Looking for the daemon…
        </CardTitle>
      </CardHeader>
    </Card>
  );
}

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
    <Card>
      <CardHeader>
        <CardTitle
          className="flex items-center gap-2"
          role="heading"
          aria-level={2}
        >
          {icon}
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      {children === null ? null : <CardContent>{children}</CardContent>}
      <CardFooter>
        <Button onClick={onRetry} disabled={checking}>
          <RotateCw
            aria-hidden
            className={checking ? "animate-spin" : undefined}
          />
          Retry
        </Button>
      </CardFooter>
    </Card>
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
    case "http":
    case "invalid_response":
    case "internal":
      return {
        title: "Something went wrong talking to the daemon",
        description: error.message,
      };
  }
}
