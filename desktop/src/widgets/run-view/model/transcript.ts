import type { RunEvent } from "@/entities/run";

/** One transcript row. All text in it is untrusted agent or tool output. */
export type Row =
  | { kind: "message"; seq: number; text: string }
  | {
      kind: "tool";
      seq: number;
      name: string;
      target: string;
      /** Seconds from the call to its result; null while it runs. */
      seconds: number | null;
      result: { text: string; lines: number; isError: boolean } | null;
    }
  | { kind: "denied"; seq: number; tool: string; command: string }
  | {
      kind: "edit";
      seq: number;
      path: string;
      added: number | null;
      removed: number | null;
    }
  | { kind: "note"; seq: number; text: string };

const str = (value: unknown): string =>
  typeof value === "string" ? value : "";
const num = (value: unknown): number | null =>
  typeof value === "number" ? value : null;

const TARGET_KEYS = [
  "command",
  "file_path",
  "notebook_path",
  "path",
  "pattern",
];

/** What a tool call works on: its command, file or pattern, from the input JSON (cut
 * at 2,000 characters by the daemon, so it may not parse; then the raw text). */
export function toolTarget(inputSummary: string): string {
  try {
    const input: unknown = JSON.parse(inputSummary);
    if (input !== null && typeof input === "object") {
      const fields = input as Record<string, unknown>;
      const key = TARGET_KEYS.find((name) => typeof fields[name] === "string");
      if (key !== undefined) {
        return str(fields[key]);
      }
    }
  } catch {
    // shown as the raw text below
  }
  return inputSummary.slice(0, 200);
}

const time = (iso: string) =>
  new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

/** The transcript of the events, in order: tool results join their call. */
export function toRows(events: readonly RunEvent[]): Row[] {
  const rows: Row[] = [];
  const calls = new Map<string, { index: number; ts: string }>();
  for (const event of events) {
    const data = event.data;
    switch (event.type) {
      case "agent.message":
        rows.push({ kind: "message", seq: event.seq, text: str(data.text) });
        break;
      case "agent.tool_call":
        calls.set(str(data.id), { index: rows.length, ts: event.ts });
        rows.push({
          kind: "tool",
          seq: event.seq,
          name: str(data.name),
          target: toolTarget(str(data.input_summary)),
          seconds: null,
          result: null,
        });
        break;
      case "agent.tool_result": {
        const call = calls.get(str(data.id));
        const row = call ? rows[call.index] : undefined;
        if (call && row?.kind === "tool") {
          const ms = new Date(event.ts).getTime() - new Date(call.ts).getTime();
          rows[call.index] = {
            ...row,
            seconds: Math.max(ms, 0) / 1000,
            result: {
              text: str(data.text),
              lines: num(data.lines) ?? 0,
              isError: data.is_error === true,
            },
          };
        }
        break;
      }
      case "agent.denied":
        rows.push({
          kind: "denied",
          seq: event.seq,
          tool: str(data.tool),
          command: toolTarget(str(data.input_summary)),
        });
        break;
      case "agent.file_edit":
        rows.push({
          kind: "edit",
          seq: event.seq,
          path: str(data.path),
          added: num(data.added),
          removed: num(data.removed),
        });
        break;
      case "agent.warning":
        rows.push({
          kind: "note",
          seq: event.seq,
          text: `Skipped a line of agent output: ${str(data.text)}`,
        });
        break;
      case "agent.rate_limit":
        if (data.status === "allowed_warning") {
          rows.push({
            kind: "note",
            seq: event.seq,
            text: "Close to the usage limit",
          });
        }
        break;
      case "run.status":
        if (data.to === "paused" && typeof data.reset_at === "string") {
          rows.push({
            kind: "note",
            seq: event.seq,
            text: `Paused by a usage limit · resumes ${time(data.reset_at)}`,
          });
        }
        break;
      case "attempt.started":
        rows.push({
          kind: "note",
          seq: event.seq,
          text: `Attempt ${String(num(data.number) ?? event.attempt ?? "")} started (${str(data.kind).replace("_", " ")})`,
        });
        break;
    }
  }
  return rows;
}

export const STEPS = [
  "worktree",
  "implement",
  "gates",
  "review",
  "policy",
  "integrate",
] as const;
export type Step = (typeof STEPS)[number];
export type StepState = "pending" | "running" | "passed" | "failed" | "skipped";

/** Each step's state from the attempt's `step` events. A step before one that has
 * started counts as passed even without its own events (the worktree of attempt 2 was
 * made before attempt 1). */
export function stepStates(
  events: readonly RunEvent[],
): Record<Step, StepState> {
  const states = Object.fromEntries(
    STEPS.map((step) => [step, "pending"]),
  ) as Record<Step, StepState>;
  for (const event of events) {
    const step = STEPS.find((name) => name === event.data.step);
    const state = event.data.state;
    if (
      event.type === "step" &&
      step !== undefined &&
      (state === "running" ||
        state === "passed" ||
        state === "failed" ||
        state === "skipped")
    ) {
      states[step] = state;
    }
  }
  const last = STEPS.findLastIndex((step) => states[step] !== "pending");
  for (const step of STEPS.slice(0, Math.max(last, 0))) {
    if (states[step] === "pending") {
      states[step] = "passed";
    }
  }
  return states;
}

/** The squash commit of a merged run, from its `integrate` event. */
export function mergedCommit(events: readonly RunEvent[]): string | null {
  const event = events.findLast((e) => e.type === "integrate");
  const commit = event ? str(event.data.commit) : "";
  return commit === "" ? null : commit.slice(0, 7);
}
