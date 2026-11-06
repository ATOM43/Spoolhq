import { ShieldAlert, TriangleAlert } from "lucide-react";

import {
  TicketChip,
  TicketStatusBadge,
  type Ticket,
  type TicketStatus,
} from "@/entities/ticket";
import { cn, formatUsage } from "@/shared/lib";

import { hours } from "../model/groups";

const WITH_REASON: readonly TicketStatus[] = ["blocked", "awaiting_approval"];

/** One ticket: chip, title, phase, dependencies, estimate, review, attempts, usage,
 * status, and the one line that says why it needs you. A click opens the drawer. */
export function TicketRow({
  ticket,
  statusOf,
  next,
  problem,
  onOpen,
}: {
  ticket: Ticket;
  /** Another ticket's status, to tell met dependencies from unmet ones. */
  statusOf: (id: string) => TicketStatus | undefined;
  next: boolean;
  /** This ticket's plan problem ("In a cycle"), if any. */
  problem: string | null;
  onOpen: (id: string) => void;
}) {
  const { meta, activity } = ticket;
  const deps = meta.depends_on ?? [];
  const reason = WITH_REASON.includes(meta.status)
    ? (activity?.reason ??
      (meta.status === "blocked"
        ? "Blocked: open it to see why"
        : "Waiting for your approval"))
    : null;
  const usage = activity
    ? formatUsage(
        activity.tokens,
        activity.cost_micro_usd == null
          ? null
          : activity.cost_micro_usd / 1_000_000,
      )
    : null;

  return (
    <tr
      data-ticket={ticket.id}
      onClick={() => {
        onOpen(ticket.id);
      }}
      className={cn(
        "cursor-pointer border-t align-top hover:bg-surface-sunken",
        problem && "bg-danger/5",
      )}
    >
      <td className="py-2 pr-3 pl-3">
        <TicketChip id={ticket.id} onOpen={onOpen} />
      </td>
      <td className="py-2 pr-3">
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              onOpen(ticket.id);
            }}
            className="text-left text-sm outline-none hover:underline focus-visible:underline"
          >
            {meta.title}
          </button>
          {next ? (
            <span className="rounded-sm bg-accent/10 px-1.5 text-xs font-medium text-accent">
              Next
            </span>
          ) : null}
        </div>
        {reason ? (
          <p className="mt-0.5 line-clamp-1 text-xs text-ink-muted">{reason}</p>
        ) : null}
        {problem ? (
          <p className="mt-0.5 flex items-center gap-1 text-xs text-danger">
            <TriangleAlert aria-hidden className="size-3" />
            {problem}
          </p>
        ) : null}
      </td>
      <td className="py-2 pr-3">
        <span className="rounded-sm bg-surface-sunken px-1.5 py-0.5 text-xs whitespace-nowrap text-ink-muted">
          Phase {meta.phase}
        </span>
      </td>
      <td className="py-2 pr-3">
        {deps.length === 0 ? (
          <span className="text-ink-muted">—</span>
        ) : (
          <span className="flex flex-wrap gap-1">
            {deps.map((dep) => {
              const met = statusOf(dep) === "done";
              return (
                <TicketChip
                  key={dep}
                  id={dep}
                  met={met}
                  label={`Open ${dep} (${met ? "done" : "not done yet"})`}
                  onOpen={onOpen}
                />
              );
            })}
          </span>
        )}
      </td>
      <td className="py-2 pr-3 text-sm whitespace-nowrap">
        {hours(meta.estimate_h)}
      </td>
      <td className="py-2 pr-3">
        {meta.review_required ? (
          <span title="Review required" className="text-warning">
            <ShieldAlert aria-hidden className="size-4" />
            <span className="sr-only">Review required</span>
          </span>
        ) : null}
      </td>
      <td className="py-2 pr-3 text-sm">
        {activity && activity.attempts > 0 ? activity.attempts : ""}
      </td>
      <td className="py-2 pr-3 text-sm whitespace-nowrap text-ink-muted">
        {usage ?? ""}
      </td>
      <td className="py-2 pr-3">
        <TicketStatusBadge status={meta.status} />
      </td>
    </tr>
  );
}
