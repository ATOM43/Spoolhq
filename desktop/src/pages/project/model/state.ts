import type { ProjectDetail } from "@/entities/project";
import type { CurrentRun } from "@/entities/run";

export type Tab = "spec" | "tickets" | "run";

/** One row of the screens spec's section 8 table: what the header offers, and where a
 * project opens. */
export type PanelState =
  | { kind: "ready"; next: string; tab: Tab }
  | {
      kind: "running";
      ticket: string;
      step: string | null;
      attempt: number;
      tab: Tab;
    }
  | { kind: "paused"; ticket: string; tab: Tab }
  | { kind: "paused_limit"; ticket: string; resumesAt: string | null; tab: Tab }
  | { kind: "idle"; reason: string; tab: Tab };

const time = (iso: string) =>
  new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

/** Why nothing runs, as the disabled Run next tooltip says it. */
function idleReason(project: ProjectDetail, specEmpty: boolean): string {
  const idle = project.idle;
  const first = idle?.ticket_ids[0] ?? "";
  switch (idle?.code) {
    case undefined:
      return specEmpty ? "Write a spec first" : "Generate a plan first";
    case "all_done":
      return "All tickets done";
    case "plan_not_approved":
      return "Approve the plan first";
    case "running":
      return "A run is already going";
    case "blocked":
      return `${first} is blocked — open it to unblock`;
    case "awaiting_approval":
      return `${first} needs approval — open it to review`;
    case "waiting":
      return `${idle.message} — finish those first`;
    case "invalid_plan":
      return `The plan has a problem: ${idle.message}`;
  }
}

export function panelState(
  project: ProjectDetail,
  current: CurrentRun | undefined,
  specEmpty: boolean,
): PanelState {
  const run = current?.run;
  if (current?.active && run) {
    if (run.status === "paused") {
      return run.reset_at
        ? {
            kind: "paused_limit",
            ticket: run.ticket_id,
            resumesAt: time(run.reset_at),
            tab: "run",
          }
        : { kind: "paused", ticket: run.ticket_id, tab: "run" };
    }
    return {
      kind: "running",
      ticket: run.ticket_id,
      step: current.phases.at(-1)?.text ?? null,
      attempt: current.attempts,
      tab: "run",
    };
  }
  if (run?.kind === "plan" && run.status === "running") {
    return { kind: "idle", reason: "Planner is running", tab: "tickets" };
  }
  if (project.next_ticket) {
    return { kind: "ready", next: project.next_ticket, tab: "tickets" };
  }
  const reason = idleReason(project, specEmpty);
  return {
    kind: "idle",
    reason,
    tab: project.total === 0 ? "spec" : "tickets",
  };
}

/** "182k tokens", or "$0.84" when the backend reports a cost. */
export function formatUsage(current: CurrentRun | undefined): string | null {
  if (!current?.run) {
    return null;
  }
  if (current.cost_micro_usd != null) {
    return `$${(current.cost_micro_usd / 1_000_000).toFixed(2)}`;
  }
  const tokens = current.input_tokens + current.output_tokens;
  if (tokens >= 1_000_000) {
    return `${(tokens / 1_000_000).toFixed(1)}M tokens`;
  }
  return tokens >= 1000
    ? `${String(Math.round(tokens / 1000))}k tokens`
    : `${String(tokens)} tokens`;
}
