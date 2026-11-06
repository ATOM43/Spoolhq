import type { Ticket, TicketStatus } from "@/entities/ticket";

/** The list's groups, in the screens spec's order (Draft first, before approval). */
export const GROUP_ORDER: readonly TicketStatus[] = [
  "draft",
  "awaiting_approval",
  "blocked",
  "running",
  "ready",
  "done",
];

export interface Filters {
  search: string;
  /** A phase number as text, or "" for every phase. */
  phase: string;
}

export const NO_FILTERS: Filters = { search: "", phase: "" };

export function matches(ticket: Ticket, filters: Filters): boolean {
  const query = filters.search.trim().toLowerCase();
  return (
    (filters.phase === "" || String(ticket.meta.phase) === filters.phase) &&
    (query === "" ||
      ticket.id.toLowerCase().includes(query) ||
      ticket.meta.title.toLowerCase().includes(query))
  );
}

/** Non-empty groups in order; tickets keep the daemon's id order. */
export function groupTickets(
  tickets: readonly Ticket[],
): { status: TicketStatus; tickets: Ticket[] }[] {
  return GROUP_ORDER.map((status) => ({
    status,
    tickets: tickets.filter((ticket) => ticket.meta.status === status),
  })).filter((group) => group.tickets.length > 0);
}

export const phases = (tickets: readonly Ticket[]): number[] =>
  [...new Set(tickets.map((ticket) => ticket.meta.phase))].sort(
    (a, b) => a - b,
  );

/** What approving the plan makes ready, for the D4 confirm. */
export function approvalSummary(tickets: readonly Ticket[]) {
  const done = new Set(
    tickets.filter((t) => t.meta.status === "done").map((t) => t.id),
  );
  const drafts = tickets.filter((ticket) => ticket.meta.status === "draft");
  return {
    phases: phases(drafts).length,
    review: drafts.filter((ticket) => ticket.meta.review_required),
    // The first draft whose dependencies are all done runs first after approval.
    firstUp:
      drafts.find((ticket) =>
        (ticket.meta.depends_on ?? []).every((dep) => done.has(dep)),
      ) ?? null,
  };
}

/** Hours without float noise: 38.5, not 38.50000001. */
export const hours = (value: number): string =>
  `${String(Math.round(value * 10) / 10)} h`;
