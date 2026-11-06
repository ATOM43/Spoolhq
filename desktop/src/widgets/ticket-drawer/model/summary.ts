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
