import { Clock, LoaderCircle } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";

import {
  useArtifact,
  useRun,
  useRunEvents,
  type RunDetail,
} from "@/entities/run";
import { TicketChip, useTickets } from "@/entities/ticket";

import {
  attemptsUsage,
  backendLabel,
  formatElapsed,
  hasResult,
  useMaxAttempts,
  useNow,
} from "../model/format";
import { liveDetails } from "../model/details";
import { mergedCommit, stepStates, toRows } from "../model/transcript";
import { Details, type DetailsTab } from "./Details";
import { Failed } from "./Failed";
import { ResultPanel } from "./ResultPanel";
import { StepIndicator } from "./Steps";
import { Transcript } from "./Transcript";

export interface RunViewProps {
  project: string;
  runId: number;
  /** Where the live stream starts when the attempt has no events yet. */
  since: number;
  /** The ticket of a newer run that started after this one (Run all), if any. */
  next: string | null;
  onViewNext: () => void;
  onOpenTicket: (id: string) => void;
  /** **Run next**, or its disabled reason, for a cancelled or interrupted run. */
  runNext: ReactNode;
}

/** V2 · Run tab, live: header, transcript (60%) and the details panel (40%). */
export function RunView(props: RunViewProps) {
  const run = useRun(props.project, props.runId);
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
      <Failed
        what="the run"
        message={run.error.message}
        onRetry={() => void run.refetch()}
      />
    );
  }
  return <Live {...props} run={run.data} />;
}

function Live({
  project,
  run,
  since,
  next,
  onViewNext,
  onOpenTicket,
  runNext,
}: RunViewProps & { run: RunDetail }) {
  const latest = run.attempts.at(-1);
  const ended = run.ended_at !== null || next !== null;
  const { attempt, events, query } = useRunEvents({
    project,
    runId: run.id,
    startAttempt: latest?.number ?? null,
    since,
    live: !ended,
  });
  const rows = useMemo(() => toRows(events), [events]);
  const steps = useMemo(() => stepStates(events), [events]);
  const live = useMemo(() => liveDetails(events), [events]);
  const [tab, setTab] = useState<DetailsTab>("gates");
  const [file, setFile] = useState<string | null>(null);
  const diff = useArtifact("diff", project, run.id, attempt, live.stamps.diff);
  const openDiff = (path: string) => {
    setFile(path);
    setTab("diff");
  };
  const now = useNow(!ended);
  const max = useMaxAttempts(project);
  const title = useTickets(project).data?.tickets.find(
    (t) => t.id === run.ticket_id,
  )?.meta.title;
  const shown = run.attempts.find((a) => a.number === attempt) ?? latest;
  const elapsed =
    (run.ended_at ? new Date(run.ended_at).getTime() : now) -
    new Date(run.started_at).getTime();
  const usage = attemptsUsage(run.attempts);

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
        {backendLabel(shown?.backend) ? (
          <span className="text-sm text-ink-muted">
            {backendLabel(shown?.backend)}
          </span>
        ) : null}
        <div className="min-w-0 flex-1">
          {hasResult(run) || next !== null ? (
            <ResultPanel
              run={run}
              commit={mergedCommit(events)}
              next={next}
              onViewNext={onViewNext}
              onOpenTicket={onOpenTicket}
              runNext={runNext}
            />
          ) : (
            <StepIndicator states={steps} />
          )}
        </div>
        <span className="flex items-center gap-1 font-mono text-sm text-ink-muted">
          <Clock aria-hidden className="size-4" />
          <span className="sr-only">Elapsed </span>
          {formatElapsed(elapsed)}
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
              message={query.error.message}
              onRetry={() => void query.refetch()}
            />
          ) : query.isPending ? (
            <p className="flex items-center gap-2 p-6 text-sm text-ink-muted">
              <LoaderCircle
                aria-hidden
                className="size-4 motion-safe:animate-spin"
              />
              Loading the transcript…
            </p>
          ) : (
            <Transcript
              key={`${String(run.id)}-${String(attempt)}`}
              rows={rows}
              diff={diff.data}
              onOpenDiff={openDiff}
            />
          )}
        </section>
        <Details
          project={project}
          runId={run.id}
          attempt={attempt}
          live={live}
          ended={ended || (shown?.ended_at != null && shown.number === attempt)}
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
