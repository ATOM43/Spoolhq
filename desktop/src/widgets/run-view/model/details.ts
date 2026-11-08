import type { RunEvent } from "@/entities/run";

export interface GateDone {
  name: string;
  command: string;
  status: string;
  duration_ms: number;
}

/** What the Gates, Review and Diff panels read from the attempt's events. */
export interface LiveDetails {
  /** The `seq` of the event after which each report changed (0: none yet). */
  stamps: { gates: number; review: number; diff: number };
  /** The gates step while it runs: the gate running now and those done before it. */
  gates: { command: string | null; done: GateDone[] } | null;
  reviewing: boolean;
}

export const NO_EVENTS: LiveDetails = {
  stamps: { gates: 0, review: 0, diff: 0 },
  gates: null,
  reviewing: false,
};

const ENDED = new Set(["passed", "failed", "skipped"]);

/** From `step` events (a gates or review step ending rewrites its report) and the
 * commit's `run.phase` event (the diff is written at the commit). */
export function liveDetails(events: readonly RunEvent[]): LiveDetails {
  const stamps = { gates: 0, review: 0, diff: 0 };
  let gates: LiveDetails["gates"] = null;
  let reviewing = false;
  for (const event of events) {
    const { data } = event;
    if (event.type === "run.phase" && data.phase === "commit") {
      stamps.diff = event.seq;
    }
    if (event.type !== "step") {
      continue;
    }
    const ended = ENDED.has(String(data.state));
    if (data.step === "gates") {
      if (ended) {
        stamps.gates = event.seq;
      }
      gates = ended
        ? null
        : {
            command:
              typeof data.command === "string"
                ? data.command || String(data.gate)
                : null,
            done: Array.isArray(data.done) ? (data.done as GateDone[]) : [],
          };
    } else if (data.step === "review") {
      if (ended) {
        stamps.review = event.seq;
      }
      reviewing = !ended;
    }
  }
  return { stamps, gates, reviewing };
}

/** "0.4s", "12s", "6m 12s". */
export function formatDuration(ms: number): string {
  if (ms < 10_000) {
    return `${(ms / 1000).toFixed(1)}s`;
  }
  const seconds = Math.round(ms / 1000);
  const m = Math.floor(seconds / 60);
  return m > 0
    ? `${String(m)}m ${String(seconds % 60).padStart(2, "0")}s`
    : `${String(seconds)}s`;
}
