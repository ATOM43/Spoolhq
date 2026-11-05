import {
  CircleCheck,
  CircleDashed,
  CircleX,
  KeyRound,
  LoaderCircle,
  RotateCw,
  TriangleAlert,
} from "lucide-react";

import { useAgents, type Agents } from "@/entities/agent";
import { Button, EmptyState, ReasonButton } from "@/shared/ui";

import { SET_UP_FIRST, useAgentBlocker } from "../model/queries";

type Backend = Agents["backends"][number];

const LABELS: Record<string, { title: string; login: string }> = {
  "claude-code-cli": {
    title: "Claude Code",
    login: "run `claude` in a terminal to log in",
  },
  "codex-cli": { title: "Codex", login: "run `codex login` in a terminal" },
  "claude-agent-sdk": {
    title: "Claude Agent SDK",
    login: "add an Anthropic API key in Accounts",
  },
};

function label(name: string) {
  return LABELS[name] ?? { title: name, login: "log in to it in a terminal" };
}

/** Amber only when it blocks the user (no backend ready at all); the optional SDK key
 * never does. */
function BackendStatus({
  backend,
  blocking,
}: {
  backend: Backend;
  blocking: boolean;
}) {
  if (!backend.installed) {
    return (
      <span className="flex items-center gap-1.5 text-ink-muted">
        <CircleDashed aria-hidden className="size-4" />
        Not installed
      </span>
    );
  }
  if (!backend.logged_in && backend.name === "claude-agent-sdk") {
    return (
      <span className="flex items-center gap-1.5 text-ink-muted">
        <KeyRound aria-hidden className="size-4" />
        Needs an API key (optional)
      </span>
    );
  }
  if (!backend.logged_in) {
    return (
      <span
        className={`flex items-center gap-1.5 ${blocking ? "text-warning" : "text-ink-muted"}`}
      >
        <CircleX aria-hidden className="size-4" />
        Not logged in — {label(backend.name).login}
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1.5 text-success">
      <CircleCheck aria-hidden className="size-4" />
      Logged in
    </span>
  );
}

/** D2 · Agents: each backend's version and login status, and Graphify. */
export function AgentsTab() {
  const agents = useAgents();
  const blocking = useAgentBlocker() !== null;

  if (agents.isPending) {
    return (
      <p className="flex items-center gap-2 text-sm text-ink-muted">
        <LoaderCircle aria-hidden className="size-4 animate-spin" />
        Looking for coding agents…
      </p>
    );
  }
  if (agents.isError) {
    return (
      <div role="alert" className="flex flex-col items-start gap-2 text-sm">
        <p className="text-danger">
          Couldn't list the agents: {agents.error.message}
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void agents.refetch()}
        >
          <RotateCw aria-hidden />
          Retry
        </Button>
      </div>
    );
  }
  const { backends, graphify } = agents.data;
  return (
    <div className="flex flex-col gap-4">
      {blocking ? (
        <p
          role="status"
          className="flex items-center gap-2 rounded-md border border-warning/40 bg-warning/10 p-3 text-sm text-warning"
        >
          <TriangleAlert aria-hidden className="size-4 shrink-0" />
          {SET_UP_FIRST}
        </p>
      ) : null}
      {backends.length === 0 ? (
        <EmptyState
          icon={<CircleDashed aria-hidden />}
          title="No coding agents found"
          description="Install Claude Code or Codex and log in, or add an Anthropic API key in Accounts."
        />
      ) : (
        <ul className="flex flex-col divide-y rounded-md border">
          {backends.map((backend) => (
            <li key={backend.name} className="flex flex-col gap-1 p-3 text-sm">
              <div className="flex items-baseline justify-between gap-2">
                <span className="font-medium">{label(backend.name).title}</span>
                <span className="font-mono text-xs text-ink-muted">
                  {backend.version ?? "—"}
                </span>
              </div>
              <BackendStatus backend={backend} blocking={blocking} />
              {backend.reason ? (
                <details className="text-xs text-ink-muted">
                  <summary className="cursor-pointer select-none">
                    Details
                  </summary>
                  <p className="mt-1 font-mono break-words">{backend.reason}</p>
                </details>
              ) : null}
            </li>
          ))}
        </ul>
      )}
      <p className="flex items-center gap-1.5 text-sm">
        {graphify.installed ? (
          <CircleCheck aria-hidden className="size-4 text-success" />
        ) : (
          <CircleDashed aria-hidden className="size-4 text-ink-muted" />
        )}
        Graphify (optional):{" "}
        {graphify.installed
          ? `found${graphify.version ? ` · ${graphify.version}` : ""}`
          : "not found"}
      </p>
      <p className="text-xs text-ink-muted">
        Which backend each project uses is set in its project.yaml.
      </p>
      <div>
        <ReasonButton
          variant="outline"
          size="sm"
          reason={agents.isFetching ? "Checking now…" : null}
          onClick={() => void agents.refetch()}
        >
          <RotateCw aria-hidden />
          Check again
        </ReasonButton>
      </div>
    </div>
  );
}
