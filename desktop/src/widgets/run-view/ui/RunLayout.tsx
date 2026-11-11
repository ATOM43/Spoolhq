import { Clock, LoaderCircle } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";

import {
  useArtifact,
  type LoadProgress,
  type RunDetail,
  type RunEvent,
} from "@/entities/run";
import { TicketChip, useTickets } from "@/entities/ticket";
import { formatElapsed } from "@/shared/lib";

import { backendLabel, useMaxAttempts } from "../model/format";
import { liveDetails, NO_EVENTS } from "../model/details";
import { stepStates, toRows, type StepState } from "../model/transcript";
import { Details, type DetailsTab } from "./Details";
import { Failed } from "./Failed";
import { StepIndicator } from "./Steps";
import { Transcript } from "./Transcript";

/**
 * The run layout the live view and a replay share: the header (ticket, attempt, backend,
 * steps or `result`, time, usage), the transcript (60%) and the details panel (40%).
 */
export function RunLayout({
  project,
  run,
  attempt,
  backend,
  events,
  query,
  progress,
  replay = false,
  ended,
  elapsedMs,
  usage,
  result,
  onOpenTicket,
}: {
  project: string;
  run: RunDetail;
  /** The attempt in view; null before the run's first. */
  attempt: number | null;
  backend: string | null | undefined;
  events: readonly RunEvent[];
  query: {
    isPending: boolean;
    isError: boolean;
    error: Error | null;
    refetch: () => unknown;
  };
  /** How far the events' load is, for a replay's loading bar. */
  progress?: LoadProgress | null;
  /** A finished attempt: steps in their final states, each report loaded once. */
  replay?: boolean;
  /** The attempt is over: a report that isn't there never will be. */
  ended: boolean;
  elapsedMs: number;
  usage: string | null;
  /** Shown in place of the step indicator (the live view's result panel). */
  result?: ReactNode;
  onOpenTicket: (id: string) => void;
}) {
  const rows = useMemo(() => toRows(events), [events]);
  const steps = useMemo(() => {
    const states = stepStates(events);
    if (replay) {
      // A step the attempt left running never finished.
      for (const [step, state] of Object.entries(states)) {
        if (state === "running") {
          states[step as keyof typeof states] = "skipped" satisfies StepState;
        }
      }
    }
    return states;
  }, [events, replay]);
  const live = useMemo(
    () => (replay ? NO_EVENTS : liveDetails(events)),
    [events, replay],
  );
  const [tab, setTab] = useState<DetailsTab>("gates");
  const [file, setFile] = useState<string | null>(null);
  const diff = useArtifact("diff", project, run.id, attempt, live.stamps.diff);
  const max = useMaxAttempts(project);
  const title = useTickets(project).data?.tickets.find(
    (t) => t.id === run.ticket_id,
  )?.meta.title;

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b bg-surface-sunken px-6 py-3">
        <div className="flex items-center gap-2">
          <TicketChip id={run.ticket_id} onOpen={onOpenTicket} />
          <button
            type="button"
            onClick={() => {
              onOpenTicket(run.ticket_id);
            }}
            className="font-medium hover:underline focus-visible:underline focus-visible:outline-none"
          >
            {title ?? run.ticket_id}
          </button>
        </div>
        {attempt !== null ? (
          <span className="text-sm text-ink-muted">
            Attempt {attempt}
            {max !== null && attempt <= max ? ` of ${String(max)}` : ""}
          </span>
        ) : null}
        {backendLabel(backend) ? (
          <span className="text-sm text-ink-muted">
            {backendLabel(backend)}
          </span>
        ) : null}
        <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
          {result ?? <StepIndicator states={steps} />}
        </div>
        <span className="flex items-center gap-1 font-mono text-sm text-ink-muted">
          <Clock aria-hidden className="size-4" />
          <span className="sr-only">Elapsed </span>
          {formatElapsed(elapsedMs)}
        </span>
        {usage ? (
          <span className="font-mono text-sm text-ink-muted">{usage}</span>
        ) : null}
      </div>
      <div className="flex min-h-0 flex-1">
        <section
          aria-label="Transcript"
          className="flex min-h-0 basis-3/5 flex-col border-r"
        >
          {query.isError ? (
            <Failed
              what="the transcript"
              message={query.error?.message ?? ""}
              onRetry={() => void query.refetch()}
            />
          ) : query.isPending ? (
            !replay ? (
              <p className="flex items-center gap-2 p-6 text-sm text-ink-muted">
                <LoaderCircle
                  aria-hidden
                  className="size-4 motion-safe:animate-spin"
                />
                Loading the transcript…
              </p>
            ) : (
              <div className="flex flex-col gap-2 p-6 text-sm text-ink-muted">
                <p role="status">
                  Loading events…
                  {progress
                    ? ` ${progress.loaded.toLocaleString("en-US")} of ${progress.total.toLocaleString("en-US")}`
                    : ""}
                </p>
                <progress
                  aria-label="Events loaded"
                  className="h-1.5 w-full max-w-sm"
                  {...(progress
                    ? { value: progress.loaded, max: progress.total }
                    : {})}
                />
              </div>
            )
          ) : (
            <Transcript
              key={`${String(run.id)}-${String(attempt)}`}
              rows={rows}
              diff={diff.data}
              onOpenDiff={(path) => {
                setFile(path);
                setTab("diff");
              }}
            />
          )}
        </section>
        <Details
          project={project}
          runId={run.id}
          attempt={attempt}
          live={live}
          ended={ended}
          diff={diff}
          tab={tab}
          onTab={setTab}
          file={file}
          onFile={setFile}
        />
      </div>
    </div>
  );
}
