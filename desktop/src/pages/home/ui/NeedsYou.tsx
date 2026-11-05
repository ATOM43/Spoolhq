import { useQueries } from "@tanstack/react-query";
import {
  CircleAlert,
  CircleDashed,
  CirclePause,
  Eye,
  FolderX,
  ListChecks,
  LoaderCircle,
  OctagonX,
  Play,
  RotateCcw,
  Trash2,
  X,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { Link } from "react-router";

import type { ProjectSummary } from "@/entities/project";
import { ticketsQuery } from "@/entities/ticket";
import { cn, formatTime, timeAgo } from "@/shared/lib";
import { Button, ConfirmDialog } from "@/shared/ui";

import { useDismissJob, useInterruptedRun } from "../model/actions";
import {
  needsYouCards,
  type NeedsYouCard,
  type NeedsYouKind,
} from "../model/needs-you";

const CHIP: Record<
  NeedsYouKind,
  { icon: ReactNode; label: string; tone: string }
> = {
  blocked: {
    icon: <OctagonX aria-hidden />,
    label: "Blocked",
    tone: "bg-danger/10 text-danger",
  },
  approval: {
    icon: <Eye aria-hidden />,
    label: "Needs approval",
    tone: "bg-warning/10 text-warning",
  },
  plan: {
    icon: <CircleDashed aria-hidden />,
    label: "Plan ready",
    tone: "bg-surface-sunken text-ink-muted",
  },
  interrupted: {
    icon: <CircleAlert aria-hidden />,
    label: "Interrupted",
    tone: "bg-warning/10 text-warning",
  },
  usage_limit: {
    icon: <CirclePause aria-hidden />,
    label: "Paused · usage limit",
    tone: "bg-warning/10 text-warning",
  },
  cleanup: {
    icon: <FolderX aria-hidden />,
    label: "Cleanup failed",
    tone: "bg-danger/10 text-danger",
  },
};

/** V1 "Needs you": one card per item, each with one action. Hidden when empty. */
export function NeedsYou({ projects }: { projects: ProjectSummary[] }) {
  const waiting = projects.filter(
    (project) => project.needs_you > 0 || project.run?.status === "interrupted",
  );
  const tickets = useQueries({
    queries: waiting.map((project) => ticketsQuery(project.name)),
  });
  const byProject = Object.fromEntries(
    waiting.map((project, index) => [
      project.name,
      tickets[index]?.data?.tickets,
    ]),
  );
  const cards = needsYouCards(projects, byProject);
  const loading = tickets.some((query) => query.isPending);
  const failed = tickets.filter((query) => query.isError).length;
  if (cards.length === 0 && !loading && failed === 0) {
    return null;
  }

  return (
    <section
      aria-labelledby="needs-you-heading"
      className="flex flex-col gap-3"
    >
      <h2
        id="needs-you-heading"
        className="flex items-center gap-2 text-lg font-semibold"
      >
        Needs you
        {cards.length > 0 ? (
          <span className="rounded-full bg-danger px-1.5 text-xs font-semibold text-surface">
            {cards.length}
          </span>
        ) : null}
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
      <ul className="grid grid-cols-[repeat(auto-fill,minmax(320px,1fr))] gap-4">
        {cards.map((card) => (
          <li key={card.key}>
            <Card card={card} />
          </li>
        ))}
      </ul>
    </section>
  );
}

function Card({ card }: { card: NeedsYouCard }) {
  const chip = CHIP[card.kind];
  return (
    <article
      aria-label={`${chip.label}: ${card.project}${card.ticket ? ` ${card.ticket.id}` : ""}`}
      className="flex h-full flex-col gap-2 rounded-lg border bg-surface p-4"
    >
      <div className="flex items-center gap-2 text-sm">
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 font-medium [&_svg]:size-3.5",
            chip.tone,
          )}
        >
          {chip.icon}
          {chip.label}
        </span>
        <span className="truncate text-ink-muted">{card.project}</span>
        {card.at ? (
          <time
            dateTime={card.at}
            title={formatTime(card.at)}
            className="ml-auto shrink-0 text-ink-muted"
          >
            {timeAgo(card.at)}
          </time>
        ) : null}
      </div>
      <p className="flex items-center gap-2 font-medium">
        {card.ticket ? (
          <span className="rounded bg-surface-sunken px-1 font-mono text-sm text-accent">
            {card.ticket.id}
          </span>
        ) : null}
        <span className="truncate">{card.ticket?.title ?? card.title}</span>
      </p>
      <p className="truncate text-sm text-ink-muted" title={card.reason}>
        {card.reason}
      </p>
      <div className="mt-auto flex gap-2 pt-1">
        <Action card={card} />
      </div>
    </article>
  );
}

function Action({ card }: { card: NeedsYouCard }) {
  const ticket = card.ticket?.id ?? "";
  const to = (tab: string) =>
    `/p/${card.project}?tab=${tab}${ticket ? `&ticket=${ticket}` : ""}`;
  switch (card.kind) {
    case "blocked":
      return (
        <LinkButton to={to("tickets")} icon={<Play aria-hidden />}>
          Unblock
        </LinkButton>
      );
    case "approval":
      return (
        <LinkButton to={to("tickets")} icon={<Eye aria-hidden />}>
          Review
        </LinkButton>
      );
    case "plan":
      return (
        <LinkButton to={to("tickets")} icon={<ListChecks aria-hidden />}>
          Review plan
        </LinkButton>
      );
    case "usage_limit":
      return (
        <LinkButton to={to("run")} icon={<Play aria-hidden />}>
          Open run
        </LinkButton>
      );
    case "interrupted":
      return <ResumeOrDiscard project={card.project} ticket={ticket} />;
    case "cleanup":
      return <Dismiss job={card.job ?? ""} />;
  }
}

function Dismiss({ job }: { job: string }) {
  const dismiss = useDismissJob(job);
  return (
    <div className="flex flex-col gap-1">
      <Button
        size="sm"
        variant="outline"
        disabled={dismiss.isPending}
        onClick={() => {
          dismiss.mutate();
        }}
      >
        <X aria-hidden />
        Dismiss
      </Button>
      {dismiss.error ? (
        <p role="alert" className="text-sm text-danger">
          {dismiss.error.message}
        </p>
      ) : null}
    </div>
  );
}

function LinkButton({
  to,
  icon,
  children,
}: {
  to: string;
  icon: ReactNode;
  children: ReactNode;
}) {
  return (
    <Button size="sm" asChild>
      <Link to={to}>
        {icon}
        {children}
      </Link>
    </Button>
  );
}

function ResumeOrDiscard({
  project,
  ticket,
}: {
  project: string;
  ticket: string;
}) {
  const action = useInterruptedRun(project, ticket);
  const [confirming, setConfirming] = useState(false);
  return (
    <div className="flex flex-col gap-1">
      <div className="flex gap-2">
        <Button
          size="sm"
          disabled={action.isPending}
          onClick={() => {
            action.mutate("resume");
          }}
        >
          <RotateCcw aria-hidden />
          Resume
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={action.isPending}
          onClick={() => {
            setConfirming(true);
          }}
        >
          <Trash2 aria-hidden />
          Discard
        </Button>
      </div>
      {action.error ? (
        <p role="alert" className="text-sm text-danger">
          {action.error.message}
        </p>
      ) : null}
      <ConfirmDialog
        open={confirming}
        title={`Discard ${ticket}'s interrupted run?`}
        consequence="Its worktree is removed and the ticket returns to Ready. Commits already on main stay."
        action="Discard run"
        destructive
        onCancel={() => {
          setConfirming(false);
        }}
        onConfirm={() => {
          setConfirming(false);
          action.mutate("discard");
        }}
      />
    </div>
  );
}
