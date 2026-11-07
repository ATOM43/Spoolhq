import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import type { RunAttempt, RunDetail } from "@/entities/run";
import { api, body } from "@/shared/api";
import { formatUsage } from "@/shared/lib";

const BACKENDS: Record<string, string> = {
  "claude-code-cli": "Claude Code",
  "codex-cli": "Codex",
  "claude-agent-sdk": "Claude Agent SDK",
};

export const backendLabel = (name: string | null | undefined): string | null =>
  name ? (BACKENDS[name] ?? name) : null;

/** "45s", "6m 12s", "1h 02m". */
export function formatElapsed(ms: number): string {
  const seconds = Math.max(Math.floor(ms / 1000), 0);
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) {
    return `${String(h)}h ${String(m).padStart(2, "0")}m`;
  }
  return m > 0 ? `${String(m)}m ${String(s)}s` : `${String(s)}s`;
}

/** Now, every second while `ticking`. */
export function useNow(ticking: boolean): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!ticking) {
      return;
    }
    const timer = setInterval(() => {
      setNow(Date.now());
    }, 1000);
    return () => {
      clearInterval(timer);
    };
  }, [ticking]);
  return now;
}

/** Tokens for attempts on a subscription, USD for those that reported a cost. */
export function attemptsUsage(attempts: readonly RunAttempt[]): string | null {
  let tokens = 0;
  let micro: number | null = null;
  for (const a of attempts) {
    if (a.cost_micro_usd == null) {
      tokens += a.input_tokens + a.output_tokens;
    } else {
      micro = (micro ?? 0) + a.cost_micro_usd;
    }
  }
  return formatUsage(tokens, micro === null ? null : micro / 1_000_000);
}

const OUTCOMES: Record<string, string> = {
  running: "Running",
  gates_failed: "Gates failed",
  changes_requested: "Changes requested",
  approved: "Approved",
  needs_human: "Needs a person",
  conflict: "Merge conflict",
  error: "Error",
  cancelled: "Cancelled",
  interrupted: "Interrupted",
};

export const attemptOutcome = (status: string): string =>
  OUTCOMES[status] ?? status;

const RUN_OUTCOMES: Record<string, string> = {
  running: "Running",
  paused: "Paused",
  awaiting_approval: "Needs approval",
  done: "Merged",
  blocked: "Blocked",
  cancelled: "Cancelled",
  interrupted: "Interrupted",
};

export const runOutcome = (status: string): string =>
  RUN_OUTCOMES[status] ?? status;

/**
 * The most attempts a run gets: the first plus its gate and review retries
 * (`limits` in project.yaml, defaults 3 and 2); null until the settings load.
 */
export function useMaxAttempts(project: string): number | null {
  const settings = useQuery({
    queryKey: ["project-settings", project],
    queryFn: () =>
      body(
        api.GET("/api/projects/{name}/settings", {
          params: { path: { name: project } },
        }),
      ),
    retry: false,
    staleTime: 60_000,
  });
  if (!settings.data) {
    return null;
  }
  const limits = settings.data.settings.limits as
    { gate_retries?: unknown; review_retries?: unknown } | undefined;
  const count = (value: unknown, fallback: number) =>
    typeof value === "number" ? value : fallback;
  return 1 + count(limits?.gate_retries, 3) + count(limits?.review_retries, 2);
}

/** Whether a run has a result to show in place of the step indicator. */
export function hasResult(run: RunDetail): boolean {
  return (
    run.status !== "running" && !(run.status === "paused" && !run.reset_at)
  );
}
