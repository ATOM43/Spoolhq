import { Check, ListChecks, RefreshCw, TriangleAlert } from "lucide-react";
import { useState } from "react";

import {
  problemLabel,
  useApprovePlan,
  useGeneratePlan,
  type Plan,
} from "@/entities/plan";
import type { Ticket } from "@/entities/ticket";
import { OpenSettingsLink, useAgentBlocker } from "@/features/settings";
import { formatTime, timeAgo } from "@/shared/lib";
import { ConfirmDialog, ReasonButton, showToast } from "@/shared/ui";

import { approvalSummary, hours } from "../model/groups";

const plural = (n: number, word: string) =>
  `${String(n)} ${word}${n === 1 ? "" : "s"}`;

/** The draft banner: size, problems as links, Approve plan (D4) and Re-plan. */
export function PlanBanner({
  project,
  plan,
  tickets,
  onOpen,
}: {
  project: string;
  plan: Plan;
  tickets: readonly Ticket[];
  onOpen: (id: string) => void;
}) {
  const [confirm, setConfirm] = useState<"approve" | "replan" | null>(null);
  const approve = useApprovePlan(project);
  const generate = useGeneratePlan(project);
  const agent = useAgentBlocker();
  const problems = plan.problems;
  const count = plural(plan.ticket_count, "ticket");
  const summary = approvalSummary(tickets);

  return (
    <section
      aria-label="Draft plan"
      className={
        problems.length > 0
          ? "flex flex-wrap items-start gap-3 rounded-lg border border-warning/40 bg-warning/10 p-4"
          : "flex flex-wrap items-start gap-3 rounded-lg border border-accent/30 bg-accent/10 p-4"
      }
    >
      {problems.length > 0 ? (
        <TriangleAlert aria-hidden className="mt-0.5 size-5 text-warning" />
      ) : (
        <ListChecks aria-hidden className="mt-0.5 size-5 text-accent" />
      )}
      <div className="min-w-0 flex-1 text-sm">
        <p className="font-semibold">
          Draft plan · {count} · {hours(plan.total_h)}
          {plan.generated_at ? (
            <span title={formatTime(plan.generated_at)}>
              {" "}
              · generated {timeAgo(plan.generated_at)}
            </span>
          ) : null}
        </p>
        {problems.length > 0 ? (
          <>
            <p>
              {plural(problems.length, "problem")} to fix before you can
              approve:
            </p>
            <ul className="mt-1 flex flex-col gap-1">
              {problems.map((problem) => (
                <li key={`${problem.code}:${problem.message}`}>
                  <button
                    type="button"
                    disabled={problem.ticket_ids.length === 0}
                    onClick={() => {
                      const first = problem.ticket_ids[0];
                      if (first) {
                        onOpen(first);
                      }
                    }}
                    className="text-left text-accent underline disabled:text-ink disabled:no-underline"
                  >
                    {problemLabel(problem)}
                  </button>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p className="text-ink-muted">
            No problems. Review the tickets, then approve to make them Ready.
          </p>
        )}
      </div>
      <div className="flex items-start gap-2">
        <ReasonButton
          variant="outline"
          reason={generate.isPending ? "Starting the planner…" : agent}
          onClick={() => {
            setConfirm("replan");
          }}
        >
          <RefreshCw aria-hidden />
          Re-plan
        </ReasonButton>
        <ReasonButton
          reason={
            problems.length > 0
              ? `Fix ${plural(problems.length, "problem")} first`
              : approve.isPending
                ? "Approving…"
                : null
          }
          onClick={() => {
            setConfirm("approve");
          }}
        >
          <Check aria-hidden />
          Approve plan
        </ReasonButton>
      </div>
      <OpenSettingsLink reason={agent} />
      <ConfirmDialog
        open={confirm === "approve"}
        title={`Approve ${count}?`}
        consequence="The tickets become Ready. Nothing runs until you press Run next or Run all, and you can still edit a Ready ticket before it starts."
        action={`Approve ${count}`}
        onCancel={() => {
          setConfirm(null);
        }}
        onConfirm={() => {
          setConfirm(null);
          approve.mutate(undefined, {
            onError: (error) => {
              showToast(`Couldn't approve the plan: ${error.message}`, "error");
            },
          });
        }}
      >
        <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 rounded-md border bg-surface-sunken p-3 text-sm">
          <dt className="text-ink-muted">Tickets</dt>
          <dd>
            {plan.ticket_count} in {plural(summary.phases, "phase")}
          </dd>
          <dt className="text-ink-muted">Estimate</dt>
          <dd>{hours(plan.total_h)}</dd>
          <dt className="text-ink-muted">Review required</dt>
          <dd className="flex flex-wrap items-center gap-1">
            {plural(summary.review.length, "ticket")}
            {summary.review.map((ticket) => (
              <span key={ticket.id} className="font-mono text-xs">
                {ticket.id}
              </span>
            ))}
          </dd>
          {summary.firstUp ? (
            <>
              <dt className="text-ink-muted">First up</dt>
              <dd className="flex items-center gap-2">
                <span className="font-mono text-xs">{summary.firstUp.id}</span>
                {summary.firstUp.meta.title}
              </dd>
            </>
          ) : null}
        </dl>
      </ConfirmDialog>
      <ConfirmDialog
        open={confirm === "replan"}
        title="Re-plan from the spec?"
        consequence="The planner drafts tickets again. Draft tickets you haven't edited are replaced; edited and approved tickets are kept."
        action="Re-plan"
        onCancel={() => {
          setConfirm(null);
        }}
        onConfirm={() => {
          setConfirm(null);
          generate.mutate(undefined, {
            onError: (error) => {
              showToast(
                `Couldn't start the planner: ${error.message}`,
                "error",
              );
            },
          });
        }}
      />
    </section>
  );
}
