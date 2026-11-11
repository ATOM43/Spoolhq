import { LoaderCircle, Play, RotateCw } from "lucide-react";
import type { ReactNode } from "react";

import {
  Outcome,
  runOutcome,
  useRunHistory,
  type RunRow,
} from "@/entities/run";
import { TicketChip, useTickets } from "@/entities/ticket";
import { formatElapsed, formatTime, formatUsage, timeAgo } from "@/shared/lib";
import { Button } from "@/shared/ui";

const HEAD = "px-3 py-2 text-left text-xs font-medium text-ink-muted";
const CELL = "px-3 py-2.5 align-middle";

/**
 * **Past runs**: the project's ticket runs, newest first, 50 a page. A row opens the
 * run's last attempt in replay, its chip the ticket drawer. Only the list is read here;
 * a run's events load when its replay opens.
 */
export function RunHistory({
  project,
  empty,
  onOpenRun,
  onOpenTicket,
}: {
  project: string;
  /** What to show when the project has no run. */
  empty: ReactNode;
  onOpenRun: (runId: number, attempt: number | null) => void;
  onOpenTicket: (id: string) => void;
}) {
  const history = useRunHistory(project);
  const tickets = useTickets(project).data?.tickets;
  if (history.isPending) {
    return (
      <ul aria-label="Loading past runs" className="flex flex-col gap-2">
        {[0, 1, 2, 3].map((row) => (
          <li
            key={row}
            aria-hidden
            className="h-10 motion-safe:animate-pulse rounded-md bg-surface-sunken"
          />
        ))}
      </ul>
    );
  }
  if (history.data === undefined) {
    return (
      <div role="alert" className="flex flex-col items-start gap-2 text-sm">
        <p className="text-danger">
          Couldn't load the past runs: {history.error.message}
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void history.refetch()}
        >
          <RotateCw aria-hidden />
          Retry
        </Button>
      </div>
    );
  }
  const rows = history.data.pages.flatMap((page) => page.items);
  if (rows.length === 0) {
    return empty;
  }
  return (
    <section aria-labelledby="past-runs" className="flex flex-col gap-3">
      <h2 id="past-runs" className="font-semibold">
        Past runs
      </h2>
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full text-sm">
          <thead className="border-b bg-surface-sunken">
            <tr>
              <th scope="col" className={HEAD}>
                Ticket
              </th>
              <th scope="col" className={HEAD}>
                Title
              </th>
              <th scope="col" className={HEAD}>
                Attempts
              </th>
              <th scope="col" className={HEAD}>
                Outcome
              </th>
              <th scope="col" className={HEAD}>
                Duration
              </th>
              <th scope="col" className={HEAD}>
                Usage
              </th>
              <th scope="col" className={HEAD}>
                Finished
              </th>
              <th scope="col" className={HEAD}>
                <span className="sr-only">Replay</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {rows.map((run) => (
              <Row
                key={run.id}
                run={run}
                title={
                  tickets?.find((t) => t.id === run.ticket_id)?.meta.title ?? ""
                }
                onOpenRun={onOpenRun}
                onOpenTicket={onOpenTicket}
              />
            ))}
          </tbody>
        </table>
        {history.hasNextPage ? (
          <div className="border-t px-3 py-2">
            <Button
              variant="ghost"
              size="sm"
              disabled={history.isFetchingNextPage}
              onClick={() => void history.fetchNextPage()}
            >
              {history.isFetchingNextPage ? (
                <LoaderCircle
                  aria-hidden
                  className="motion-safe:animate-spin"
                />
              ) : null}
              Load more
            </Button>
            {history.isError ? (
              <span role="alert" className="ml-2 text-sm text-danger">
                Couldn't load more: {history.error.message}
              </span>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}

function Row({
  run,
  title,
  onOpenRun,
  onOpenTicket,
}: {
  run: RunRow;
  title: string;
  onOpenRun: (runId: number, attempt: number | null) => void;
  onOpenTicket: (id: string) => void;
}) {
  const open = () => {
    onOpenRun(run.id, run.last_attempt);
  };
  const when = run.ended_at ?? run.started_at;
  const usage = formatUsage(
    run.tokens,
    run.cost_micro_usd == null ? null : run.cost_micro_usd / 1_000_000,
  );
  return (
    <tr onClick={open} className="cursor-pointer hover:bg-surface-sunken">
      <td className={CELL}>
        <TicketChip id={run.ticket_id} onOpen={onOpenTicket} />
      </td>
      <td className={CELL}>{title}</td>
      <td className={`${CELL} font-mono text-ink-muted`}>{run.attempts}</td>
      <td className={CELL}>
        <Outcome status={run.status} label={runOutcome(run.status)} />
      </td>
      <td className={`${CELL} font-mono text-ink-muted`}>
        {run.ended_at
          ? formatElapsed(
              new Date(run.ended_at).getTime() -
                new Date(run.started_at).getTime(),
            )
          : "—"}
      </td>
      <td className={`${CELL} font-mono text-ink-muted`}>{usage ?? "—"}</td>
      <td className={`${CELL} text-ink-muted`} title={formatTime(when)}>
        {timeAgo(when)}
      </td>
      <td className={`${CELL} text-right`}>
        {/* The row's keyboard way in; its click bubbles to the row. */}
        <Button
          variant="ghost"
          size="sm"
          aria-label={`Replay ${run.ticket_id}, run ${String(run.id)}`}
        >
          <Play aria-hidden />
          Replay
        </Button>
      </td>
    </tr>
  );
}
