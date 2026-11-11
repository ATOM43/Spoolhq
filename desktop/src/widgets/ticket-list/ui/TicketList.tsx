import {
  ChevronDown,
  ChevronRight,
  FilePen,
  LoaderCircle,
  Plus,
  RotateCw,
  SearchX,
  Sparkles,
} from "lucide-react";
import { useState, type ReactNode } from "react";

import { usePlan, useGeneratePlan, type Plan } from "@/entities/plan";
import type { ProjectDetail } from "@/entities/project";
import { useCurrentRun } from "@/entities/run";
import {
  STATUS_LOOK,
  useTickets,
  type Ticket,
  type TicketStatus,
} from "@/entities/ticket";
import { OpenSettingsLink, useAgentBlocker } from "@/features/settings";
import {
  Button,
  EmptyState,
  Input,
  ReasonButton,
  showToast,
} from "@/shared/ui";

import {
  groupTickets,
  matches,
  NO_FILTERS,
  phases,
  type Filters,
} from "../model/groups";
import { PlanBanner } from "./PlanBanner";
import { TicketRow } from "./TicketRow";

const PROBLEM_TAG: Record<string, string> = {
  cycle: "In a cycle",
  missing_done_when: "No “Done when”",
  unknown_dependency: "Depends on a ticket that doesn't exist",
  duplicate_id: "Id used by more than one file",
  invalid_ticket: "The file is invalid",
};

/** Each ticket's first plan problem, as its row says it. */
function problemTags(plan: Plan | undefined): Map<string, string> {
  const tags = new Map<string, string>();
  for (const problem of plan?.problems ?? []) {
    for (const id of problem.ticket_ids) {
      if (!tags.has(id)) {
        tags.set(id, PROBLEM_TAG[problem.code] ?? problem.message);
      }
    }
  }
  return tags;
}

/** V2 · Tickets tab: plan review, board and approval queue in one list. */
export function TicketList({
  project,
  onOpen,
  onAdd,
  onOpenSpec,
}: {
  project: ProjectDetail;
  onOpen: (id: string) => void;
  /** Open the drawer on a new, empty ticket. */
  onAdd: () => void;
  onOpenSpec: () => void;
}) {
  const tickets = useTickets(project.name);
  const plan = usePlan(project.name);
  const running = useCurrentRun(project.name).data?.active ?? false;
  const add = (
    <ReasonButton
      variant="outline"
      reason={
        plan.data?.state === "planning"
          ? "Wait for the planner to finish"
          : running
            ? "Wait for the run to finish"
            : null
      }
      onClick={onAdd}
    >
      <Plus aria-hidden />
      Add ticket
    </ReasonButton>
  );

  if (tickets.isPending || plan.isPending) {
    return (
      <p className="flex items-center gap-2 text-sm text-ink-muted">
        <LoaderCircle aria-hidden className="size-4 animate-spin" />
        Loading tickets…
      </p>
    );
  }
  if (tickets.isError || plan.isError) {
    const error = tickets.error ?? plan.error;
    return (
      <div role="alert" className="flex flex-col items-start gap-2 text-sm">
        <p className="text-danger">
          Couldn't load the tickets: {error?.message}
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            void tickets.refetch();
            void plan.refetch();
          }}
        >
          <RotateCw aria-hidden />
          Retry
        </Button>
      </div>
    );
  }
  if (plan.data.state === "planning") {
    return <Planning project={project.name} />;
  }
  if (tickets.data.tickets.length === 0 && plan.data.problems.length === 0) {
    return project.has_spec ? (
      <NoPlan project={project.name} add={add} />
    ) : (
      <EmptyState
        icon={<FilePen aria-hidden />}
        title="Write a spec and generate a plan, or add a ticket yourself."
        description="The spec (CONTEXT.md) says what the project should do; a ticket you add runs without one."
        action={
          <span className="flex flex-wrap items-center justify-center gap-2">
            <Button onClick={onOpenSpec}>Open Spec</Button>
            {add}
          </span>
        }
      />
    );
  }
  return (
    <Board
      project={project}
      plan={plan.data}
      tickets={tickets.data.tickets}
      add={add}
      onOpen={onOpen}
    />
  );
}

function Board({
  project,
  plan,
  tickets,
  add,
  onOpen,
}: {
  project: ProjectDetail;
  plan: Plan;
  tickets: Ticket[];
  add: ReactNode;
  onOpen: (id: string) => void;
}) {
  const [filters, setFilters] = useState<Filters>(NO_FILTERS);
  const allDone = tickets.every((ticket) => ticket.meta.status === "done");
  // "Show done" and the Done group's own toggle are one state; all done opens it.
  const [showDone, setShowDone] = useState(allDone);
  const shown = tickets.filter((ticket) => matches(ticket, filters));
  const statuses = new Map(tickets.map((t) => [t.id, t.meta.status]));
  const tags = problemTags(plan);
  const filtered = filters.search !== "" || filters.phase !== "";

  return (
    <div className="flex flex-col gap-4">
      {plan.state === "draft" ? (
        <PlanBanner
          project={project.name}
          plan={plan}
          tickets={tickets}
          onOpen={onOpen}
        />
      ) : null}
      <div className="flex flex-wrap items-center gap-3">
        <Input
          type="search"
          aria-label="Search tickets"
          placeholder="Search tickets"
          className="w-60"
          value={filters.search}
          onChange={(event) => {
            setFilters({ ...filters, search: event.target.value });
          }}
        />
        <select
          aria-label="Phase"
          className="h-9 rounded-md border bg-surface px-2 text-sm"
          value={filters.phase}
          onChange={(event) => {
            setFilters({ ...filters, phase: event.target.value });
          }}
        >
          <option value="">All phases</option>
          {phases(tickets).map((phase) => (
            <option key={phase} value={String(phase)}>
              Phase {phase}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={showDone}
            onChange={(event) => {
              setShowDone(event.target.checked);
            }}
          />
          Show done
        </label>
        <span className="ml-auto">{add}</span>
      </div>
      {shown.length === 0 ? (
        <EmptyState
          icon={<SearchX aria-hidden />}
          title="No tickets match."
          description="Try another search or phase."
          action={
            <Button
              variant="outline"
              onClick={() => {
                setFilters(NO_FILTERS);
              }}
            >
              Clear filters
            </Button>
          }
        />
      ) : (
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-ink-muted">
              <tr>
                <th className="py-2 pr-3 pl-3 font-medium">ID</th>
                <th className="py-2 pr-3 font-medium">Ticket</th>
                <th className="py-2 pr-3 font-medium">Phase</th>
                <th className="py-2 pr-3 font-medium">Depends on</th>
                <th className="py-2 pr-3 font-medium">Est.</th>
                <th className="py-2 pr-3 font-medium">Review</th>
                <th className="py-2 pr-3 font-medium">Attempts</th>
                <th className="py-2 pr-3 font-medium">Usage</th>
                <th className="py-2 pr-3 font-medium">Status</th>
              </tr>
            </thead>
            {groupTickets(shown).map((group) => (
              <Group
                key={group.status}
                status={group.status}
                count={group.tickets.length}
                open={group.status !== "done" || showDone}
                onToggle={
                  group.status === "done"
                    ? () => {
                        setShowDone(!showDone);
                      }
                    : null
                }
              >
                {group.tickets.map((ticket) => (
                  <TicketRow
                    key={ticket.file_name}
                    ticket={ticket}
                    statusOf={(id) => statuses.get(id)}
                    next={project.next_ticket === ticket.id}
                    problem={tags.get(ticket.id) ?? null}
                    onOpen={onOpen}
                  />
                ))}
              </Group>
            ))}
          </table>
        </div>
      )}
      {filtered && shown.length > 0 ? (
        <Button
          variant="link"
          size="sm"
          className="self-start"
          onClick={() => {
            setFilters(NO_FILTERS);
          }}
        >
          Clear filters
        </Button>
      ) : null}
    </div>
  );
}

function Group({
  status,
  count,
  open,
  onToggle,
  children,
}: {
  status: TicketStatus;
  count: number;
  open: boolean;
  /** Null: the group can't be collapsed. */
  onToggle: (() => void) | null;
  children: ReactNode;
}) {
  const { icon, tone, label } = STATUS_LOOK[status];
  const heading = (
    <span className="flex items-center gap-2">
      <span className={`flex items-center gap-1.5 [&_svg]:size-3.5 ${tone}`}>
        {icon}
        {label}
      </span>
      <span className="text-ink-muted">
        {count} {count === 1 ? "ticket" : "tickets"}
      </span>
    </span>
  );
  return (
    <tbody aria-label={label} data-group={status}>
      <tr className="border-t bg-surface-sunken text-xs">
        <th colSpan={9} scope="rowgroup" className="py-2 pl-3 font-medium">
          {onToggle ? (
            <button
              type="button"
              aria-expanded={open}
              onClick={onToggle}
              className="flex items-center gap-1"
            >
              {open ? (
                <ChevronDown aria-hidden className="size-3.5" />
              ) : (
                <ChevronRight aria-hidden className="size-3.5" />
              )}
              {heading}
            </button>
          ) : (
            heading
          )}
        </th>
      </tr>
      {open ? children : null}
    </tbody>
  );
}

/** The planner is drafting tickets: skeleton rows and its latest progress line. */
function Planning({ project }: { project: string }) {
  const current = useCurrentRun(project);
  const progress =
    current.data?.run?.kind === "plan"
      ? current.data.phases.at(-1)?.text
      : null;
  return (
    <div className="flex flex-col gap-4" aria-busy="true">
      <div
        role="status"
        className="flex items-center gap-2 rounded-lg border border-accent/30 bg-accent/10 p-4 text-sm"
      >
        <LoaderCircle aria-hidden className="size-4 animate-spin text-accent" />
        <span className="font-medium">Planner is running</span>
        {progress ? <span className="text-ink-muted">· {progress}</span> : null}
      </div>
      <ul aria-hidden className="flex flex-col gap-2">
        {[0, 1, 2, 3, 4].map((row) => (
          <li
            key={row}
            className="h-9 animate-pulse rounded-md bg-surface-sunken"
          />
        ))}
      </ul>
    </div>
  );
}

function NoPlan({ project, add }: { project: string; add: ReactNode }) {
  const generate = useGeneratePlan(project);
  const agent = useAgentBlocker();
  const blocker = generate.isPending ? "Starting the planner…" : agent;
  return (
    <EmptyState
      icon={<Sparkles aria-hidden />}
      title="No plan yet."
      description="The planner reads the spec and drafts tickets for you to review and approve."
      action={
        <span className="flex flex-col items-center gap-2">
          <span className="flex flex-wrap items-center justify-center gap-2">
            <ReasonButton
              reason={blocker}
              onClick={() => {
                generate.mutate(undefined, {
                  onError: (error) => {
                    showToast(
                      `Couldn't start the planner: ${error.message}`,
                      "error",
                    );
                  },
                });
              }}
            >
              <Sparkles aria-hidden />
              Generate plan
            </ReasonButton>
            {add}
          </span>
          <OpenSettingsLink reason={agent} />
        </span>
      }
    />
  );
}
