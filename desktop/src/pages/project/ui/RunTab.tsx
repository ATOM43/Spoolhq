import { LoaderCircle, StepForward } from "lucide-react";
import { useState } from "react";

import { useAgentBlocker } from "@/features/settings";
import type { CurrentRun } from "@/entities/run";
import { ReasonButton } from "@/shared/ui";
import {
  FinishedAttempt,
  LastRun,
  LoadFailed,
  NoRunsYet,
  RunView,
} from "@/widgets/run-view";

import { useRunAction } from "../model/run";
import type { PanelState } from "../model/state";

/**
 * The Run tab: the run being watched (live, then its result), else a finished
 * `?attempt=N`, the last run with Run next, or "No runs yet". A run that started while
 * this one was watched (Run all) is offered through the result panel's **View T16**.
 */
export function RunTab({
  project,
  current,
  state,
  attempt,
  ticket,
  onOpenTicket,
  onShowTickets,
  onShowCurrent,
}: {
  project: string;
  current: {
    data: CurrentRun | undefined;
    isPending: boolean;
    error: Error | null;
    refetch: () => unknown;
  };
  state: PanelState;
  /** `?attempt=` from the URL, or null. */
  attempt: number | null;
  /** `?ticket=` from the URL, or null. */
  ticket: string | null;
  onOpenTicket: (id: string) => void;
  onShowTickets: () => void;
  onShowCurrent: () => void;
}) {
  const [watched, setWatched] = useState<number | null>(null);
  const run = current.data?.run?.kind === "ticket" ? current.data.run : null;
  const live = current.data?.active && run ? run : null;
  if (live && watched === null) {
    setWatched(live.id);
  }
  const runNext = <RunNext project={project} state={state} />;

  if (current.isPending) {
    return (
      <p className="flex items-center gap-2 p-6 text-sm text-ink-muted">
        <LoaderCircle aria-hidden className="size-4 motion-safe:animate-spin" />
        Loading the run…
      </p>
    );
  }
  if (current.error) {
    return (
      <LoadFailed
        what="the run"
        message={current.error.message}
        onRetry={() => void current.refetch()}
      />
    );
  }
  const attemptOf = ticket ?? run?.ticket_id;
  if (attempt !== null && attemptOf) {
    return (
      <FinishedAttempt
        project={project}
        ticket={attemptOf}
        attempt={attempt}
        onOpenTicket={onOpenTicket}
        onShowCurrent={onShowCurrent}
      />
    );
  }
  if (watched !== null) {
    const next = live && live.id !== watched ? live : null;
    return (
      <RunView
        key={watched}
        project={project}
        runId={watched}
        since={current.data?.latest_seq ?? 0}
        next={next?.ticket_id ?? null}
        onViewNext={() => {
          setWatched(next?.id ?? watched);
        }}
        onOpenTicket={onOpenTicket}
        runNext={runNext}
      />
    );
  }
  return run ? (
    <LastRun run={run} onOpenTicket={onOpenTicket} runNext={runNext} />
  ) : (
    <div className="p-6">
      <NoRunsYet onShowTickets={onShowTickets} />
    </div>
  );
}

/** **Run next (T11)**, or disabled with the header's reason. */
function RunNext({ project, state }: { project: string; state: PanelState }) {
  const action = useRunAction(project);
  const agent = useAgentBlocker();
  const reason =
    state.kind === "idle"
      ? state.reason
      : state.kind === "ready"
        ? (agent ??
          (action.isPending ? "Waiting for the daemon to answer" : null))
        : "A run is already going";
  return (
    <ReasonButton
      size="sm"
      reason={reason}
      onClick={() => {
        action.mutate("next");
      }}
    >
      <StepForward aria-hidden />
      Run next{state.kind === "ready" ? ` (${state.next})` : ""}
    </ReasonButton>
  );
}
