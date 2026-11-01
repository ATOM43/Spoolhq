import { useQueries } from "@tanstack/react-query";
import { CircleAlert, CirclePause, Hand, LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router";

import type { ProjectSummary } from "@/entities/project";
import { ticketsQuery } from "@/entities/ticket";

interface Item {
  key: string;
  project: string;
  text: string;
}

/** Blocked tickets, tickets awaiting approval and paused runs, each kind listed once. */
export function NeedsYou({ projects }: { projects: ProjectSummary[] }) {
  const waiting = projects.filter((project) => project.needs_you > 0);
  const tickets = useQueries({
    queries: waiting.map((project) => ticketsQuery(project.name)),
  });

  const blocked: Item[] = [];
  const approval: Item[] = [];
  tickets.forEach((query, index) => {
    const project = waiting[index]?.name ?? "";
    for (const ticket of query.data?.tickets ?? []) {
      const item = {
        key: `${project}/${ticket.id}`,
        project,
        text: `${ticket.id} · ${ticket.meta.title}`,
      };
      if (ticket.meta.status === "blocked") {
        blocked.push(item);
      } else if (ticket.meta.status === "awaiting_approval") {
        approval.push(item);
      }
    }
  });
  const paused: Item[] = projects
    .filter((project) => project.run_state === "paused")
    .map((project) => ({
      key: project.name,
      project: project.name,
      text: "Run paused",
    }));

  const loading = tickets.some((query) => query.isPending);
  const failed = tickets.filter((query) => query.isError).length;
  if (waiting.length === 0 && paused.length === 0) {
    return null;
  }

  return (
    <section
      aria-labelledby="needs-you-heading"
      className="flex flex-col gap-3"
    >
      <h2 id="needs-you-heading" className="text-lg font-semibold">
        Needs you
      </h2>
      {loading ? (
        <p className="flex items-center gap-2 text-sm text-ink-muted">
          <LoaderCircle aria-hidden className="size-4 animate-spin" />
          Loading tickets…
        </p>
      ) : null}
      {failed > 0 ? (
        <p role="alert" className="text-sm text-danger">
          Couldn't load the tickets of{" "}
          {failed === 1 ? "one project" : `${String(failed)} projects`}; open
          the project to see them.
        </p>
      ) : null}
      <Group
        title="Blocked"
        icon={<CircleAlert aria-hidden />}
        items={blocked}
      />
      <Group
        title="Awaiting approval"
        icon={<Hand aria-hidden />}
        items={approval}
      />
      <Group
        title="Paused runs"
        icon={<CirclePause aria-hidden />}
        items={paused}
      />
    </section>
  );
}

function Group({
  title,
  icon,
  items,
}: {
  title: string;
  icon: ReactNode;
  items: Item[];
}) {
  if (items.length === 0) {
    return null;
  }
  return (
    <div className="flex flex-col gap-1.5">
      <h3 className="flex items-center gap-1.5 text-sm font-medium text-warning [&_svg]:size-4">
        {icon}
        <span className="text-ink">{title}</span>
      </h3>
      <ul className="flex flex-col gap-1">
        {items.map((item) => (
          <li key={item.key}>
            <Link
              to={`/p/${item.project}`}
              className="flex gap-2 rounded-md border bg-surface px-3 py-2 text-sm hover:bg-surface-sunken"
            >
              <span className="font-mono text-ink-muted">{item.project}</span>
              <span className="truncate">{item.text}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
