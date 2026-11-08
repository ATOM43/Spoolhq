import type { RunLimits } from "@/entities/run";
import type { TicketDetail } from "@/entities/ticket";

/**
 * "Starts attempt 3 of 6 · 1 review retry left": the attempt the note starts, out of
 * the run's most (left out past it: attempt numbers are per ticket), and the review
 * retries the run has left (all of them again when the reset is on).
 */
export function nextAttemptLine(
  detail: TicketDetail | undefined,
  limits: RunLimits | null,
  reset: boolean,
): string | null {
  const last = detail?.attempts.at(-1);
  if (!detail?.run || !last || limits === null) {
    return null;
  }
  const next = last.number + 1;
  const left = reset
    ? limits.reviewRetries
    : (detail.review_retries_left ?? limits.reviewRetries);
  const of =
    next <= limits.maxAttempts ? ` of ${String(limits.maxAttempts)}` : "";
  const retries =
    left === 0
      ? "no review retries left"
      : `${String(left)} review ${left === 1 ? "retry" : "retries"} left`;
  return `Starts attempt ${String(next)}${of} · ${retries}`;
}
