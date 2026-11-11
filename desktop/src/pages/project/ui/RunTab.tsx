import { LoaderCircle, StepForward } from "lucide-react";
import { useState } from "react";

import { useAgentBlocker } from "@/features/settings";
import type { CurrentRun } from "@/entities/run";
import { ReasonButton } from "@/shared/ui";
import { RunHistory } from "@/widgets/run-history";
import {
  LastRun,
  LoadFailed,
  NoRunsYet,
  Replay,
  RunView,
} from "@/widgets/run-view";

import { useRunAction } from "../model/run";
import type { PanelState } from "../model/state";

/**
 * The Run tab: a replay (`?run=7&attempt=2`) first, so a run that starts meanwhile never
 * takes it over; else the run being watched (live, then its result); else the last run
 * with Run next and the past runs, or "No runs yet". A run that started while another
 * was watched (Run all) is offered through the result panel's **View T16**.
 */
export function RunTab({
  project,
  current,
  state,
  replay,
  onReplay,
  onOpenTicket,
  onShowTickets,
}: {
  project: string;
  current: {
    data: CurrentRun | undefined;
    isPending: boolean;
    error: Error | null;
    refetch: () => unknown;
  };
  state: PanelState;
  /** `?run=` and `?attempt=` from the URL: the attempt replayed, or null. */
  replay: { runId: number; attempt: number | null } | null;
  /** Open a replay, or (null) leave it. */
  onReplay: (replay: { runId: number; attempt: number | null } | null) => void;
  onOpenTicket: (id: string) => void;
  onShowTickets: () => void;
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
  if (replay !== null) {
    return (
      <Replay
        project={project}
        runId={replay.runId}
        attempt={replay.attempt}
        active={live !== null}
        onAttempt={(attempt) => {
          onReplay({ runId: replay.runId, attempt });
        }}
        onShowCurrent={() => {
          setWatched(live?.id ?? watched);
          onReplay(null);
        }}
        onShowPast={() => {
          setWatched(null);
          onReplay(null);
        }}
        onOpenTicket={onOpenTicket}
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
        onShowPast={() => {
          setWatched(null);
        }}
        runNext={runNext}
      />
    );
  }
  const history = (
    <RunHistory
      project={project}
      empty={<NoRunsYet onShowTickets={onShowTickets} />}
      onOpenRun={(runId, attempt) => {
        onReplay({ runId, attempt });
      }}
      onOpenTicket={onOpenTicket}
    />
  );
  // The latest run may be a plan run while ticket runs exist: the table still lists them.
  return run ? (
    <LastRun run={run} onOpenTicket={onOpenTicket} runNext={runNext}>
      {history}
    </LastRun>
  ) : (
    <div className="overflow-auto p-6">{history}</div>
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
