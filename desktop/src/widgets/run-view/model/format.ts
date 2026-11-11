import { useEffect, useState } from "react";

import { useRunLimits, type RunAttempt, type RunDetail } from "@/entities/run";
import { formatUsage } from "@/shared/lib";

const BACKENDS: Record<string, string> = {
  "claude-code-cli": "Claude Code",
  "codex-cli": "Codex",
  "claude-agent-sdk": "Claude Agent SDK",
};

export const backendLabel = (name: string | null | undefined): string | null =>
  name ? (BACKENDS[name] ?? name) : null;

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

/** The most attempts a run gets (first plus retries); null until the settings load. */
export function useMaxAttempts(project: string): number | null {
  return useRunLimits(project)?.maxAttempts ?? null;
}

/** Whether a run has a result to show in place of the step indicator. */
export function hasResult(run: RunDetail): boolean {
  return (
    run.status !== "running" && !(run.status === "paused" && !run.reset_at)
  );
}
