import type { ProjectSummary } from "@/entities/project";

export type NeedsYouKind =
  "blocked" | "approval" | "plan" | "interrupted" | "usage_limit";

export interface NeedsYouCard {
  key: string;
  kind: NeedsYouKind;
  project: string;
  ticket: { id: string; title: string } | null;
  /** The card's title when there is no ticket ("Draft plan ready for review"). */
  title: string | null;
  reason: string;
  /** When it started needing the user, if known. */
  at: string | null;
}

interface TicketLike {
  id: string;
  meta: { title: string; status: string };
}

/** Home shows at most this many cards (screens spec, V1). */
export const MAX_CARDS = 6;

const sentence = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

const time = (iso: string) =>
  new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

/** Everything waiting for the user, across projects: blocked tickets, tickets awaiting
 * approval, draft plans, runs a stopped daemon interrupted, usage-limit pauses. */
export function needsYouCards(
  projects: ProjectSummary[],
  tickets: Record<string, TicketLike[] | undefined>,
): NeedsYouCard[] {
  const cards: NeedsYouCard[] = [];
  for (const project of projects) {
    if (project.settings_error) {
      continue; // the project card already says what to fix
    }
    const run = project.run;
    // The project's latest run explains its ticket, when it is that ticket's.
    const runOf = (id: string) => (run?.ticket_id === id ? run : null);
    for (const ticket of tickets[project.name] ?? []) {
      const status = ticket.meta.status;
      if (status !== "blocked" && status !== "awaiting_approval") {
        continue;
      }
      const latest = runOf(ticket.id);
      const blocked = status === "blocked";
      cards.push({
        key: `${project.name}/${ticket.id}`,
        kind: blocked ? "blocked" : "approval",
        project: project.name,
        ticket: { id: ticket.id, title: ticket.meta.title },
        title: null,
        reason: latest?.reason
          ? sentence(latest.reason)
          : blocked
            ? "Blocked · open it to see why"
            : "Waiting for your review",
        at: latest?.ended_at ?? null,
      });
    }
    if (project.draft > 0) {
      cards.push({
        key: `${project.name}/plan`,
        kind: "plan",
        project: project.name,
        ticket: null,
        title: "Draft plan ready for review",
        reason: `Planner finished: ${String(project.draft)} tickets · ${String(project.remaining_h)} h`,
        at: project.last_activity ?? null,
      });
    }
    if (
      run?.kind === "ticket" &&
      run.status === "interrupted" &&
      project.run_step !== "discarded"
    ) {
      const title = tickets[project.name]?.find(
        (ticket) => ticket.id === run.ticket_id,
      )?.meta.title;
      cards.push({
        key: `${project.name}/interrupted`,
        kind: "interrupted",
        project: project.name,
        ticket: { id: run.ticket_id, title: title ?? "" },
        title: null,
        reason: sentence(run.reason ?? "The run was interrupted"),
        at: run.ended_at ?? null,
      });
    }
    if (project.run_state === "paused" && run?.reset_at) {
      cards.push({
        key: `${project.name}/paused`,
        kind: "usage_limit",
        project: project.name,
        ticket: { id: run.ticket_id, title: "" },
        title: null,
        reason: `Usage limit · resumes ${time(run.reset_at)}`,
        at: project.last_activity ?? null,
      });
    }
  }
  return cards.slice(0, MAX_CARDS);
}
