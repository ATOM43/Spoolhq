import { ListTodo, Play } from "lucide-react";
import type { ReactNode } from "react";

import { Outcome, runOutcome, type RunDetail } from "@/entities/run";
import { TicketChip } from "@/entities/ticket";
import { formatTime, timeAgo } from "@/shared/lib";
import { Button, EmptyState } from "@/shared/ui";

/** No run ever: the next step is approving the plan and pressing Run next. */
export function NoRunsYet({ onShowTickets }: { onShowTickets: () => void }) {
  return (
    <EmptyState
      icon={<Play aria-hidden />}
      title="No runs yet."
      description="Approve the plan, then press Run next."
      action={
        <Button onClick={onShowTickets}>
          <ListTodo aria-hidden />
          Open Tickets
        </Button>
      }
    />
  );
}

/** Nothing running: the last run in one line, and Run next (or why it can't). */
export function LastRun({
  run,
  onOpenTicket,
  runNext,
  children,
}: {
  run: Pick<RunDetail, "ticket_id" | "status" | "started_at" | "ended_at">;
  onOpenTicket: (id: string) => void;
  runNext: ReactNode;
  /** The past-runs table, under the summary. */
  children?: ReactNode;
}) {
  const when = run.ended_at ?? run.started_at;
  return (
    <div className="flex flex-col gap-6 overflow-auto p-6">
      <section
        aria-label="Last run"
        className="flex flex-wrap items-center gap-3 rounded-lg border p-4"
      >
        <span className="text-sm text-ink-muted">Last run</span>
        <TicketChip id={run.ticket_id} onOpen={onOpenTicket} />
        <Outcome status={run.status} label={runOutcome(run.status)} />
        <span className="text-sm text-ink-muted" title={formatTime(when)}>
          {timeAgo(when)}
        </span>
        <div className="ml-auto">{runNext}</div>
      </section>
      {children}
    </div>
  );
}
