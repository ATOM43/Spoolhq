import { Circle, CircleCheck, CircleX, LoaderCircle, X } from "lucide-react";
import { useEffect, type ReactNode } from "react";

import {
  splitDoneWhen,
  TicketChip,
  TicketStatusBadge,
  useLatestReview,
  useTickets,
  type ItemVerdict,
  type Ticket,
} from "@/entities/ticket";
import { Button, Markdown } from "@/shared/ui";

/**
 * The ticket drawer (screens spec section 7), read-only for now: 520 px from the right,
 * over the tab content. Esc or ✕ closes it; the page keeps `?ticket=` in the URL.
 */
export function TicketDrawer({
  project,
  ticketId,
  onOpen,
  onClose,
}: {
  project: string;
  ticketId: string;
  onOpen: (id: string) => void;
  onClose: () => void;
}) {
  const tickets = useTickets(project);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      // A dialog open on top (a confirm) takes Escape for itself.
      if (event.key === "Escape" && !document.querySelector("dialog[open]")) {
        onClose();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
    };
  }, [onClose]);

  const all = tickets.data?.tickets ?? [];
  const ticket = all.find((t) => t.id === ticketId);

  return (
    <aside
      aria-label={`Ticket ${ticketId}`}
      className="absolute inset-y-0 right-0 z-40 flex w-[520px] max-w-full flex-col border-l bg-surface shadow-lg"
    >
      <header className="flex items-start gap-2 border-b p-4">
        <span className="rounded-sm bg-surface-sunken px-1.5 py-0.5 font-mono text-xs">
          {ticketId}
        </span>
        <h2 className="min-w-0 flex-1 font-semibold">
          {ticket?.meta.title ?? ""}
        </h2>
        {ticket ? <TicketStatusBadge status={ticket.meta.status} /> : null}
        <Button
          variant="ghost"
          size="icon"
          aria-label="Close"
          onClick={onClose}
        >
          <X aria-hidden />
        </Button>
      </header>
      <div className="flex min-h-0 flex-1 flex-col gap-6 overflow-auto p-4">
        {tickets.isPending ? (
          <p className="flex items-center gap-2 text-sm text-ink-muted">
            <LoaderCircle aria-hidden className="size-4 animate-spin" />
            Loading {ticketId}…
          </p>
        ) : tickets.isError ? (
          <p role="alert" className="text-sm text-danger">
            Couldn't load the ticket: {tickets.error.message}
          </p>
        ) : ticket ? (
          <Details
            project={project}
            ticket={ticket}
            all={all}
            onOpen={onOpen}
          />
        ) : (
          <div className="flex flex-col items-start gap-3">
            <p>This ticket no longer exists.</p>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        )}
      </div>
    </aside>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section aria-label={title} className="flex flex-col gap-2">
      <h3 className="text-xs font-semibold tracking-wide text-ink-muted uppercase">
        {title}
      </h3>
      {children}
    </section>
  );
}

const VERDICT: Record<
  "met" | "not_met" | "none",
  { icon: ReactNode; label: string }
> = {
  met: {
    icon: <CircleCheck aria-hidden className="text-success" />,
    label: "Met",
  },
  not_met: {
    icon: <CircleX aria-hidden className="text-danger" />,
    label: "Not met",
  },
  none: {
    icon: <Circle aria-hidden className="text-ink-muted" />,
    label: "Not reviewed yet",
  },
};

function Details({
  project,
  ticket,
  all,
  onOpen,
}: {
  project: string;
  ticket: Ticket;
  all: readonly Ticket[];
  onOpen: (id: string) => void;
}) {
  const { scope, doneWhen } = splitDoneWhen(ticket.body);
  const review = useLatestReview(project, ticket.activity?.run_id ?? null);
  // Matched by text, so an item edited after the review shows as not reviewed yet.
  const verdicts = new Map<string, ItemVerdict>(
    (review.data ?? []).map((v) => [v.item, v]),
  );
  const statusOf = new Map(all.map((t) => [t.id, t.meta.status]));
  const dependsOn = ticket.meta.depends_on ?? [];
  const blocks = all.filter((t) =>
    (t.meta.depends_on ?? []).includes(ticket.id),
  );

  const chips = (ids: readonly string[]) =>
    ids.length === 0 ? (
      <p className="text-sm text-ink-muted">None</p>
    ) : (
      <ul className="flex flex-col gap-1">
        {ids.map((id) => {
          const status = statusOf.get(id);
          return (
            <li key={id} className="flex items-center gap-2 text-sm">
              <TicketChip id={id} met={status === "done"} onOpen={onOpen} />
              {status ? (
                <TicketStatusBadge status={status} />
              ) : (
                <span className="text-danger">Doesn't exist</span>
              )}
            </li>
          );
        })}
      </ul>
    );

  return (
    <>
      <Section title="Scope">
        {scope === "" ? (
          <p className="text-sm text-ink-muted">No scope written.</p>
        ) : (
          <Markdown source={scope} />
        )}
      </Section>
      <Section title="Done when">
        {doneWhen.length === 0 ? (
          <p className="text-sm text-danger">
            No “Done when” checklist: the reviewer has nothing to check.
          </p>
        ) : (
          <ul className="flex flex-col gap-2">
            {doneWhen.map((item, index) => {
              const verdict = verdicts.get(item.text);
              const kind = verdict ? (verdict.met ? "met" : "not_met") : "none";
              return (
                <li
                  key={`${String(index)}:${item.text}`}
                  data-review={kind}
                  className="flex flex-col gap-0.5 text-sm"
                >
                  <span className="flex items-start gap-2">
                    <span className="mt-0.5 [&_svg]:size-4">
                      {VERDICT[kind].icon}
                    </span>
                    <span className="flex-1">{item.text}</span>
                    <span className="text-xs whitespace-nowrap text-ink-muted">
                      {VERDICT[kind].label}
                    </span>
                  </span>
                  {verdict && !verdict.met ? (
                    <span className="pl-6 text-xs text-ink-muted">
                      {verdict.reason}
                    </span>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </Section>
      <Section title="Dependencies">
        <p className="text-xs text-ink-muted">Depends on</p>
        {chips(dependsOn)}
        <p className="text-xs text-ink-muted">Blocks</p>
        {chips(blocks.map((t) => t.id))}
      </Section>
      <Section title="Details">
        <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 text-sm">
          <dt className="text-ink-muted">Phase</dt>
          <dd>{ticket.meta.phase}</dd>
          <dt className="text-ink-muted">Estimate</dt>
          <dd>{ticket.meta.estimate_h} h</dd>
          <dt className="text-ink-muted">Review required</dt>
          <dd>{ticket.meta.review_required ? "Yes" : "No"}</dd>
        </dl>
      </Section>
      <p className="text-sm text-ink-muted">Actions and editing come in T37</p>
    </>
  );
}
