import { RotateCw, SquareTerminal, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";

import {
  ruleLabel,
  type Ticket,
  type TicketAttempt,
  type TicketDetail,
} from "@/entities/ticket";
import { formatTime, formatUsage, timeAgo } from "@/shared/lib";
import { Button, CopyButton } from "@/shared/ui";

import { attemptSummary, lastAttempt } from "../model/summary";
import { AttemptChecks } from "./AttemptChecks";

/** Loading and error states for the sections that read the ticket's detail. */
export function DetailState({
  query,
  children,
}: {
  query: {
    isPending: boolean;
    isError: boolean;
    error: Error | null;
    refetch: () => unknown;
  };
  children: ReactNode;
}) {
  if (query.isPending) {
    return <p className="text-sm text-ink-muted">Loading…</p>;
  }
  if (query.isError) {
    return (
      <div role="alert" className="flex items-center gap-2 text-sm">
        <span className="text-danger">
          Couldn't load: {query.error?.message}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void query.refetch()}
        >
          <RotateCw aria-hidden />
          Retry
        </Button>
      </div>
    );
  }
  return children;
}

/** Section 1: why a blocked or waiting ticket needs a person. */
export function NeedsYouSection({
  project,
  ticket,
  detail,
  onShowRun,
}: {
  project: string;
  ticket: Ticket;
  detail: TicketDetail;
  onShowRun: (attempt?: number) => void;
}) {
  const run = detail.run;
  const attempt = lastAttempt(detail);
  const git = detail.git;
  const rules = run?.policy?.rules ?? [];
  return (
    <div className="flex flex-col gap-2 rounded-md border border-warning/40 bg-warning/10 p-3 text-sm">
      <h3 className="flex items-center gap-1.5 font-semibold">
        <TriangleAlert aria-hidden className="size-4 text-warning" />
        Why it needs you
      </h3>
      {ticket.meta.status === "blocked" ? (
        <p>{attemptSummary(detail) ?? "Blocked; the run log has no reason."}</p>
      ) : (
        <>
          {rules.length > 0 ? (
            <ul
              aria-label="Rules that fired"
              className="flex flex-wrap gap-1.5"
            >
              {rules.map((hit) => (
                <li
                  key={hit.rule}
                  title={hit.detail}
                  className="rounded-sm border border-warning px-1.5 py-0.5 text-xs text-warning"
                >
                  {ruleLabel(hit)}
                </li>
              ))}
            </ul>
          ) : null}
          <p>
            {git.pr_number != null
              ? "Delivered as a pull request: it merges when it is merged on GitHub."
              : "Gates and review are done; it merges once you approve it."}
          </p>
          {git.pr_number != null ? (
            <p className="text-ink-muted">
              PR #{git.pr_number} · {git.pr_state ?? "open"} ·{" "}
              {git.pr_checked_at ? (
                <span title={formatTime(git.pr_checked_at)}>
                  checked {timeAgo(git.pr_checked_at)}
                </span>
              ) : (
                "not checked since the daemon started"
              )}
            </p>
          ) : null}
        </>
      )}
      {attempt ? <AttemptChecks project={project} attempt={attempt} /> : null}
      {attempt ? (
        <Button
          variant="link"
          size="sm"
          className="self-start px-0"
          onClick={() => {
            onShowRun(attempt.number);
          }}
        >
          <SquareTerminal aria-hidden />
          Open attempt {attempt.number} in the Run tab
        </Button>
      ) : null}
    </div>
  );
}

const OUTCOME: Record<string, string> = {
  running: "Running",
  gates_failed: "Gates failed",
  changes_requested: "Changes requested",
  approved: "Approved",
  needs_human: "Held for a person",
  conflict: "Conflict",
  error: "Stopped",
  cancelled: "Cancelled",
  interrupted: "Interrupted",
};

function duration(start: string, end: string | null | undefined): string {
  if (!end) {
    return "—";
  }
  const seconds = Math.max(
    0,
    Math.round((Date.parse(end) - Date.parse(start)) / 1000),
  );
  const minutes = Math.floor(seconds / 60);
  return `${String(minutes)}m ${String(seconds % 60).padStart(2, "0")}s`;
}

/** Section 6: every attempt; a row opens it in the Run tab. */
export function AttemptsSection({
  project,
  attempts,
  onShowRun,
}: {
  project: string;
  attempts: readonly TicketAttempt[];
  onShowRun: (attempt?: number) => void;
}) {
  if (attempts.length === 0) {
    return <p className="text-sm text-ink-muted">No attempts yet.</p>;
  }
  return (
    <ul className="flex flex-col divide-y rounded-md border text-sm">
      {[...attempts].reverse().map((a, index) => (
        <li key={a.number}>
          <button
            type="button"
            aria-label={`Attempt ${String(a.number)}: ${OUTCOME[a.status] ?? a.status}. Open it in the Run tab`}
            onClick={() => {
              onShowRun(a.number);
            }}
            className="grid w-full grid-cols-[2.5rem_1fr_4.5rem_1fr] gap-x-3 gap-y-0.5 px-3 py-2 text-left outline-none hover:bg-surface-sunken focus-visible:ring-[3px] focus-visible:ring-accent/50"
          >
            <span className="font-mono">#{a.number}</span>
            <span title={formatTime(a.started_at)}>
              {new Date(a.started_at).toLocaleTimeString()}
            </span>
            <span>{duration(a.started_at, a.ended_at)}</span>
            <span>{OUTCOME[a.status] ?? a.status}</span>
            <span />
            <span className="text-ink-muted">{a.backend ?? "—"}</span>
            <span className="col-span-2 text-ink-muted">
              {formatUsage(
                a.input_tokens + a.output_tokens,
                a.cost_micro_usd == null ? null : a.cost_micro_usd / 1_000_000,
              ) ?? "No usage"}
            </span>
          </button>
          {index === 0 && a.status !== "running" ? (
            <div className="px-3 pb-2 pl-[4.25rem]">
              <AttemptChecks project={project} attempt={a} />
            </div>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

/** Section 7's rows: branch, commits, tag and pull request. */
export function GitSection({
  git,
  branch,
}: {
  git: TicketDetail["git"];
  branch: string;
}) {
  const rows: [string, ReactNode][] = [
    [
      "Branch",
      git.branch ? (
        <code className="font-mono">{git.branch}</code>
      ) : (
        "No branch"
      ),
    ],
    [
      "Commits",
      git.commits != null
        ? `${String(git.commits)} ahead of ${branch} · ${String(git.diff_lines ?? 0)} changed lines`
        : "—",
    ],
    [
      "Merged as",
      git.commit ? (
        <span className="flex items-center gap-1">
          <code className="font-mono">{git.commit.slice(0, 7)}</code>
          <CopyButton text={git.commit_url ?? git.commit} label="Copy commit" />
        </span>
      ) : (
        "Not merged"
      ),
    ],
    ["Tag", git.tag ? <code className="font-mono">{git.tag}</code> : "—"],
    [
      "Pull request",
      git.pr_number != null ? (
        <span className="flex items-center gap-1">
          #{git.pr_number} · {git.pr_state}
          {git.pr_url ? (
            <CopyButton text={git.pr_url} label="Copy PR link" />
          ) : null}
        </span>
      ) : (
        "None"
      ),
    ],
  ];
  return (
    <dl className="grid grid-cols-[auto_1fr] items-center gap-x-6 gap-y-1 text-sm">
      {rows.map(([term, value]) => (
        <div key={term} className="contents">
          <dt className="text-ink-muted">{term}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
