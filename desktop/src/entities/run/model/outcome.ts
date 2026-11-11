const RUN_OUTCOMES: Record<string, string> = {
  running: "Running",
  paused: "Paused",
  awaiting_approval: "Needs approval",
  done: "Merged",
  blocked: "Blocked",
  cancelled: "Cancelled",
  interrupted: "Interrupted",
};

/** A run's status as the words the app shows. */
export const runOutcome = (status: string): string =>
  RUN_OUTCOMES[status] ?? status;
