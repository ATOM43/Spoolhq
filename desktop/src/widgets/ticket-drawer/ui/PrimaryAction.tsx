import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Check,
  CircleCheck,
  CircleX,
  Copy,
  LoaderCircle,
  Play,
  RotateCcw,
  SquareTerminal,
  Unlock,
} from "lucide-react";
import { useState, type ReactNode } from "react";

import { NoteDialog, type NoteKind } from "@/features/agent-note";
import { OpenSettingsLink, useAgentBlocker } from "@/features/settings";
import { useProject } from "@/entities/project";
import { useCurrentRun } from "@/entities/run";
import {
  ruleLabel,
  TicketChip,
  type Ticket,
  type TicketDetail,
} from "@/entities/ticket";
import { api, queryKeys } from "@/shared/api";
import { Button, ConfirmDialog, ReasonButton, useCopy } from "@/shared/ui";

import { attemptSummary } from "../model/summary";

export const RUN_GOING = "A run is already going";

const short = (sha: string) => sha.slice(0, 7);

/**
 * The drawer header's one primary action for the ticket's status (spec section 7),
 * plus Request changes next to Approve and merge. Every disabled action says why.
 */
export function PrimaryAction({
  project,
  ticket,
  detail,
  all,
  onOpen,
  onShowRun,
}: {
  project: string;
  ticket: Ticket;
  detail: TicketDetail | undefined;
  all: readonly Ticket[];
  onOpen: (id: string) => void;
  onShowRun: (attempt?: number) => void;
}) {
  const queryClient = useQueryClient();
  const current = useCurrentRun(project);
  const branch = useProject(project).data?.default_branch ?? "main";
  const agent = useAgentBlocker();
  const [note, setNote] = useState<NoteKind | null>(null);
  const [confirm, setConfirm] = useState(false);
  const refresh = () =>
    Promise.all(
      [
        queryKeys.projects,
        queryKeys.runs(project),
        queryKeys.tickets(project),
      ].map((queryKey) => queryClient.invalidateQueries({ queryKey })),
    );
  const path = { name: project, ticket_id: ticket.id };
  const start = useMutation({
    mutationFn: () =>
      api.POST("/api/projects/{name}/run/ticket/{ticket_id}", {
        params: { path },
      }),
    onSuccess: () => {
      onShowRun();
    },
    onSettled: refresh,
  });
  const approve = useMutation({
    mutationFn: () =>
      api.POST("/api/projects/{name}/tickets/{ticket_id}/approve", {
        params: { path },
      }),
    onSettled: refresh,
  });
  const running = current.data?.active ? RUN_GOING : null;
  const pending =
    start.isPending || approve.isPending
      ? "Waiting for the daemon to answer"
      : null;
  const agentReason = running ?? agent ?? pending;
  const status = ticket.meta.status;
  const run = detail?.run ?? null;
  const git = detail?.git;

  if (status === "draft" || status === "ready") {
    const statusOf = new Map(all.map((t) => [t.id, t.meta.status]));
    const unmet = (ticket.meta.depends_on ?? []).filter(
      (id) => statusOf.get(id) !== "done",
    );
    const reason =
      unmet.length > 0
        ? `Waits for ${unmet.join(", ")}`
        : status === "draft"
          ? "Approve the plan first"
          : agentReason;
    return (
      <Row>
        <ReasonButton
          reason={reason}
          onClick={() => {
            start.mutate();
          }}
        >
          <Play aria-hidden />
          Run this ticket
        </ReasonButton>
        {unmet.length > 0 ? (
          <span className="flex items-center gap-1 text-sm text-ink-muted">
            Waits for
            {unmet.map((id) => (
              <TicketChip key={id} id={id} met={false} onOpen={onOpen} />
            ))}
          </span>
        ) : null}
        <OpenSettingsLink reason={reason} />
        <Failure error={start.error} what="start the run" />
      </Row>
    );
  }
  if (status === "running") {
    return (
      <Row>
        <Button
          onClick={() => {
            onShowRun();
          }}
        >
          <SquareTerminal aria-hidden />
          Open run
        </Button>
      </Row>
    );
  }
  if (status === "blocked") {
    return (
      <Row>
        <ReasonButton
          reason={agentReason}
          onClick={() => {
            setNote("unblock");
          }}
        >
          <Unlock aria-hidden />
          Unblock
        </ReasonButton>
        <OpenSettingsLink reason={agentReason} />
        <NoteDialog
          project={project}
          ticketId={ticket.id}
          kind="unblock"
          open={note === "unblock"}
          summary={<p>{attemptSummary(detail) ?? "Blocked."}</p>}
          onClose={() => {
            setNote(null);
          }}
          onStarted={() => {
            onShowRun();
          }}
        />
      </Row>
    );
  }
  if (status === "done") {
    return (
      <Row>
        <CopyAction
          text={git?.commit_url ?? git?.commit ?? ""}
          label={
            git?.commit_url
              ? "Copy commit link"
              : `Copy commit${git?.commit ? ` ${short(git.commit)}` : ""}`
          }
          reason={
            detail && !git?.commit
              ? "No merge commit is recorded for this ticket"
              : !detail
                ? "Loading the commit…"
                : null
          }
        />
      </Row>
    );
  }
  // Needs approval: the pull request on GitHub, or a person here.
  if (run?.pr_number != null) {
    return (
      <Row>
        <CopyAction
          text={run.pr_url ?? ""}
          label={`Copy PR link (#${String(run.pr_number)})`}
          reason={null}
        />
        <span className="text-sm text-ink-muted">
          PR {git?.pr_state ?? "open"}
        </span>
      </Row>
    );
  }
  const rules = run?.policy?.rules ?? [];
  const merged = approve.isSuccess ? mergeResult(ticket, detail) : null;
  return (
    <Row>
      <ReasonButton
        reason={running ?? pending}
        onClick={() => {
          setConfirm(true);
        }}
      >
        <Check aria-hidden />
        Approve and merge
      </ReasonButton>
      <ReasonButton
        variant="outline"
        reason={agentReason}
        onClick={() => {
          setNote("changes");
        }}
      >
        <RotateCcw aria-hidden />
        Request changes
      </ReasonButton>
      <OpenSettingsLink reason={agentReason} />
      {merged}
      <Failure error={approve.error} what="merge" />
      <ConfirmDialog
        open={confirm}
        title={`Merge ${ticket.id} into ${branch}?`}
        consequence={
          git?.diff_lines != null
            ? `${String(git.diff_lines)} changed lines in ${String(git.commits ?? 0)} commits are squashed onto ${branch}.`
            : `The ticket's changes are squashed onto ${branch}.`
        }
        action={`Merge into ${branch}`}
        onCancel={() => {
          setConfirm(false);
        }}
        onConfirm={() => {
          setConfirm(false);
          approve.mutate();
        }}
      >
        {rules.length > 0 ? (
          <ul
            aria-label="Rules that fired"
            className="mt-3 flex flex-wrap gap-1.5"
          >
            {rules.map((hit) => (
              <li
                key={hit.rule}
                className="rounded-sm border border-warning px-1.5 py-0.5 text-xs text-warning"
              >
                {ruleLabel(hit)}
              </li>
            ))}
          </ul>
        ) : null}
      </ConfirmDialog>
      <NoteDialog
        project={project}
        ticketId={ticket.id}
        kind="changes"
        open={note === "changes"}
        summary={
          <p>
            {rules.length > 0
              ? `Held by the merge policy: ${rules.map(ruleLabel).join(", ")}`
              : "Waiting for your approval."}
          </p>
        }
        onClose={() => {
          setNote(null);
        }}
        onStarted={() => {
          onShowRun();
        }}
      />
    </Row>
  );
}

/** After Approve and merge: merged, failed (the run blocked) or still merging. */
function mergeResult(
  ticket: Ticket,
  detail: TicketDetail | undefined,
): ReactNode {
  if (ticket.meta.status === "done" && detail?.git.commit) {
    return (
      <p
        role="status"
        className="flex items-center gap-1.5 text-sm text-success"
      >
        <CircleCheck aria-hidden className="size-4" />
        Merged as <code className="font-mono">{short(detail.git.commit)}</code>
      </p>
    );
  }
  if (ticket.meta.status === "blocked") {
    return (
      <p role="alert" className="flex items-center gap-1.5 text-sm text-danger">
        <CircleX aria-hidden className="size-4" />
        Couldn't merge: {detail?.run?.reason ?? "the integration stopped"}
      </p>
    );
  }
  return (
    <p
      role="status"
      className="flex items-center gap-1.5 text-sm text-ink-muted"
    >
      <LoaderCircle aria-hidden className="size-4 animate-spin" />
      Merging…
    </p>
  );
}

function Row({ children }: { children: ReactNode }) {
  return <div className="flex flex-wrap items-center gap-2">{children}</div>;
}

function Failure({ error, what }: { error: Error | null; what: string }) {
  return error ? (
    <p role="alert" className="w-full text-sm text-danger">
      Couldn't {what}: {error.message}
    </p>
  ) : null;
}

/** Links are copied, not opened: the app has no opener plugin. */
function CopyAction({
  text,
  label,
  reason,
}: {
  text: string;
  label: string;
  reason: string | null;
}) {
  const { state, copy } = useCopy(text);
  return (
    <>
      <ReasonButton reason={reason} onClick={() => void copy()}>
        {state === "copied" ? <Check aria-hidden /> : <Copy aria-hidden />}
        {label}
      </ReasonButton>
      {state === "copied" ? (
        <span role="status" className="text-sm text-ink-muted">
          Copied
        </span>
      ) : state === "failed" ? (
        <span role="alert" className="text-sm text-danger">
          Couldn't copy: <code className="font-mono select-all">{text}</code>
        </span>
      ) : null}
    </>
  );
}
