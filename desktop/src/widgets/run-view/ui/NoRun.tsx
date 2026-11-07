import {
  CircleAlert,
  CircleCheck,
  CircleSlash,
  CircleX,
  Eye,
  History,
  ListTodo,
  LoaderCircle,
  Play,
  type LucideIcon,
} from "lucide-react";
import { useEffect, type ReactNode } from "react";

import type { RunDetail } from "@/entities/run";
import { TicketChip, useTicketDetail } from "@/entities/ticket";
import { formatTime, timeAgo } from "@/shared/lib";
import { Button, EmptyState } from "@/shared/ui";

import { attemptOutcome, runOutcome } from "../model/format";
import { Failed } from "./RunView";

const ICONS: Record<string, { icon: LucideIcon; tone: string }> = {
  done: { icon: CircleCheck, tone: "text-success" },
  approved: { icon: CircleCheck, tone: "text-success" },
  blocked: { icon: CircleX, tone: "text-danger" },
  gates_failed: { icon: CircleX, tone: "text-danger" },
  error: { icon: CircleX, tone: "text-danger" },
  awaiting_approval: { icon: Eye, tone: "text-warning" },
  needs_human: { icon: Eye, tone: "text-warning" },
  cancelled: { icon: CircleSlash, tone: "text-ink-muted" },
};

function Outcome({ status, label }: { status: string; label: string }) {
  const { icon: Icon, tone } = ICONS[status] ?? {
    icon: CircleAlert,
    tone: "text-warning",
  };
  return (
    <span className={`flex items-center gap-1 text-sm font-medium ${tone}`}>
      <Icon aria-hidden className="size-4" />
      {label}
    </span>
  );
}

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
}: {
  run: Pick<RunDetail, "ticket_id" | "status" | "started_at" | "ended_at">;
  onOpenTicket: (id: string) => void;
  runNext: ReactNode;
}) {
  const when = run.ended_at ?? run.started_at;
  return (
    <div className="flex flex-col gap-4 p-6">
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
      <p className="flex items-center gap-2 text-sm text-ink-muted">
        <History aria-hidden className="size-4" />
        The list of past runs comes in T40.
      </p>
    </div>
  );
}

/** `?attempt=N` of a finished attempt: its outcome until replay exists (T40). The
 * attempt that is still running is the live view: `onShowCurrent` goes there. */
export function FinishedAttempt({
  project,
  ticket,
  attempt,
  onOpenTicket,
  onShowCurrent,
}: {
  project: string;
  ticket: string;
  attempt: number;
  onOpenTicket: (id: string) => void;
  onShowCurrent: () => void;
}) {
  const detail = useTicketDetail(project, ticket);
  const found = detail.data?.ticket.attempts.find((a) => a.number === attempt);
  const running = found?.status === "running";
  useEffect(() => {
    if (running) {
      onShowCurrent();
    }
  }, [running, onShowCurrent]);
  if (detail.isPending) {
    return (
      <p className="flex items-center gap-2 p-6 text-sm text-ink-muted">
        <LoaderCircle aria-hidden className="size-4 motion-safe:animate-spin" />
        Loading attempt {attempt}…
      </p>
    );
  }
  if (detail.isError) {
    return (
      <Failed
        what={`attempt ${String(attempt)}`}
        message={detail.error.message}
        onRetry={() => void detail.refetch()}
      />
    );
  }
  return (
    <div className="flex flex-col items-start gap-3 p-6">
      <section
        aria-label={`Attempt ${String(attempt)}`}
        className="flex flex-wrap items-center gap-3 rounded-lg border p-4"
      >
        <TicketChip id={ticket} onOpen={onOpenTicket} />
        <span className="text-sm font-medium">Attempt {attempt}</span>
        {found ? (
          <>
            <Outcome
              status={found.status}
              label={attemptOutcome(found.status)}
            />
            {found.ended_at ? (
              <span
                className="text-sm text-ink-muted"
                title={formatTime(found.ended_at)}
              >
                finished {timeAgo(found.ended_at)}
              </span>
            ) : null}
          </>
        ) : (
          <span className="text-sm text-ink-muted">
            {ticket} has no attempt {attempt}.
          </span>
        )}
      </section>
      <p className="text-sm text-ink-muted">Full replay comes in T40.</p>
      <Button variant="outline" size="sm" onClick={onShowCurrent}>
        Show current run
      </Button>
    </div>
  );
}
