import { ArrowLeft, ArrowRight, LoaderCircle } from "lucide-react";
import { useEffect, type ReactNode } from "react";

import {
  Outcome,
  runOutcome,
  useRun,
  useRunEvents,
  type RunDetail,
} from "@/entities/run";
import { formatTime } from "@/shared/lib";
import { Button } from "@/shared/ui";

import { attemptOutcome, attemptsUsage } from "../model/format";
import { Failed } from "./Failed";
import { RunLayout } from "./RunLayout";

const time = (iso: string) =>
  new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

interface ReplayProps {
  project: string;
  runId: number;
  /** The attempt's number (per ticket); null opens the run's last attempt. */
  attempt: number | null;
  /** A run is going: the banner offers **Show current run**. */
  active: boolean;
  onAttempt: (attempt: number) => void;
  onShowCurrent: () => void;
  onShowPast: () => void;
  onOpenTicket: (id: string) => void;
}

/**
 * A past attempt in the live view's layout, read-only: a grey banner, final step
 * states, the stored events (paged in, never streamed) and the attempt's reports. No
 * run controls. The attempt that is still running isn't replayed: `onShowCurrent`.
 */
export function Replay(props: ReplayProps) {
  const run = useRun(props.project, props.runId);
  const leave = props.active ? (
    <Button variant="outline" size="sm" onClick={props.onShowCurrent}>
      Show current run
    </Button>
  ) : (
    <Button variant="outline" size="sm" onClick={props.onShowPast}>
      <ArrowLeft aria-hidden />
      Back to past runs
    </Button>
  );
  if (run.isPending) {
    return (
      <p className="flex items-center gap-2 p-6 text-sm text-ink-muted">
        <LoaderCircle aria-hidden className="size-4 motion-safe:animate-spin" />
        Loading the run…
      </p>
    );
  }
  if (run.isError) {
    return (
      <div className="flex flex-col items-start">
        <Failed
          what="the run"
          message={run.error.message}
          onRetry={() => void run.refetch()}
        />
        <div className="px-6">{leave}</div>
      </div>
    );
  }
  const number = props.attempt ?? run.data.attempts.at(-1)?.number ?? null;
  return (
    // Keyed: each attempt has its own events, scroll position and open rows.
    <Loaded
      key={number}
      {...props}
      run={run.data}
      number={number}
      leave={leave}
    />
  );
}

function Loaded({
  project,
  run,
  number,
  leave,
  onAttempt,
  onShowCurrent,
  onOpenTicket,
}: ReplayProps & {
  run: RunDetail;
  number: number | null;
  leave: ReactNode;
}) {
  const index = run.attempts.findIndex((a) => a.number === number);
  const shown = run.attempts[index];
  const previous = run.attempts[index - 1];
  const next = index >= 0 ? run.attempts[index + 1] : undefined;
  const running = shown?.status === "running" && run.ended_at === null;
  useEffect(() => {
    if (running) {
      onShowCurrent(); // the running attempt is the live view's
    }
  }, [running, onShowCurrent]);
  const missing = number !== null && shown === undefined;
  const { events, query, progress } = useRunEvents({
    project,
    runId: run.id,
    startAttempt: missing ? null : number,
    since: 0,
    live: false,
  });
  const last = run.attempts.at(-1);
  // The run's outcome is its last attempt's; an earlier attempt has its own verdict.
  const outcome =
    shown && shown !== last
      ? { status: shown.status, label: attemptOutcome(shown.status) }
      : { status: run.status, label: runOutcome(run.status) };
  const finished = missing ? null : (shown?.ended_at ?? run.ended_at);
  const start = shown?.started_at ?? run.started_at;

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div
        role="region"
        aria-label="Replay"
        className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b bg-surface-sunken px-6 py-2 text-sm text-ink-muted"
      >
        <span title={finished ? formatTime(finished) : undefined}>
          {shown && last
            ? `Viewing attempt ${String(shown.number)} of ${String(last.number)}`
            : missing
              ? `${run.ticket_id}'s run has no attempt ${String(number)}`
              : `Viewing ${run.ticket_id}'s run · no attempt started`}
          {finished ? ` · finished ${time(finished)}` : ""}
        </span>
        {missing ? null : <Outcome {...outcome} />}
        <div className="ml-auto flex flex-wrap items-center gap-2">
          {previous ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                onAttempt(previous.number);
              }}
            >
              <ArrowLeft aria-hidden />
              Previous attempt
            </Button>
          ) : null}
          {next ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                onAttempt(next.number);
              }}
            >
              Next attempt
              <ArrowRight aria-hidden />
            </Button>
          ) : null}
          {leave}
        </div>
      </div>
      {missing || running ? null : (
        <RunLayout
          project={project}
          run={run}
          attempt={number}
          backend={shown?.backend}
          events={events}
          query={query}
          progress={progress}
          replay
          ended
          elapsedMs={
            finished
              ? new Date(finished).getTime() - new Date(start).getTime()
              : 0
          }
          usage={shown ? attemptsUsage([shown]) : null}
          onOpenTicket={onOpenTicket}
        />
      )}
    </div>
  );
}
