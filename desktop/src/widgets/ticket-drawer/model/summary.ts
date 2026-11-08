import type { GatesReport, ReviewReport } from "@/entities/run";
import type { TicketAttempt, TicketDetail } from "@/entities/ticket";

/** The latest run's last attempt, which the blocked reason is about. */
export function lastAttempt(
  detail: TicketDetail | undefined,
): TicketAttempt | null {
  const runId = detail?.run?.id;
  const ofRun = (detail?.attempts ?? []).filter((a) => a.run_id === runId);
  return ofRun.at(-1) ?? null;
}

/** "Attempt 3: gates failed after 2 retries", for the note dialog and Why it needs you. */
export function attemptSummary(
  detail: TicketDetail | undefined,
): string | null {
  const reason = detail?.run?.reason;
  if (!reason) {
    return null;
  }
  const attempt = lastAttempt(detail);
  return attempt ? `Attempt ${String(attempt.number)}: ${reason}` : reason;
}

export type CheckTone = "passed" | "failed" | "waiting" | "none";

/** "Gates: 2 of 3 passed · test failed"; skipped gates (not set) don't count. */
export function gatesLine(report: GatesReport | null): {
  tone: CheckTone;
  text: string;
} {
  if (report === null) {
    return { tone: "none", text: "Gates: not run" };
  }
  if (report.stopped) {
    return { tone: "none", text: "Gates: not run (the agent stopped early)" };
  }
  const ran = report.results.filter((r) => r.state !== "skipped");
  const passed = ran.filter((r) => r.state === "passed").length;
  const failed = ran
    .filter((r) => r.state !== "passed")
    .map(
      (r) => `${r.name} ${r.state === "timed_out" ? "timed out" : "failed"}`,
    );
  return {
    tone: failed.length > 0 ? "failed" : "passed",
    text: [
      `Gates: ${String(passed)} of ${String(ran.length)} passed`,
      ...failed,
    ].join(" · "),
  };
}

const VERDICT = {
  approve: { tone: "passed", label: "approved" },
  changes_requested: { tone: "failed", label: "changes requested" },
  needs_human: { tone: "waiting", label: "needs a person" },
} as const;

/** "Review: changes requested · 4 of 5 met". */
export function reviewLine(report: ReviewReport | null): {
  tone: CheckTone;
  text: string;
} {
  if (report === null) {
    return { tone: "none", text: "Review: not run" };
  }
  if (report.verdict == null) {
    return { tone: "none", text: "Review: stopped early" };
  }
  const { tone, label } = VERDICT[report.verdict];
  const met = report.items.filter((item) => item.met).length;
  return {
    tone,
    text: `Review: ${label} · ${String(met)} of ${String(report.items.length)} met`,
  };
}
