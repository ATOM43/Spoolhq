import { History, LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";

import { useRun, useRunEvents, type RunDetail } from "@/entities/run";
import { Button } from "@/shared/ui";

import { attemptsUsage, hasResult, useNow } from "../model/format";
import { mergedCommit } from "../model/transcript";
import { Failed } from "./Failed";
import { ResultPanel } from "./ResultPanel";
import { RunLayout } from "./RunLayout";

export interface RunViewProps {
  project: string;
  runId: number;
  /** Where the live stream starts when the attempt has no events yet. */
  since: number;
  /** The ticket of a newer run that started after this one (Run all), if any. */
  next: string | null;
  onViewNext: () => void;
  onOpenTicket: (id: string) => void;
  /** Leave the ended run for the past-runs table. */
  onShowPast: () => void;
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
  onShowPast,
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
  const now = useNow(!ended);
  const shown = run.attempts.find((a) => a.number === attempt) ?? latest;
  return (
    <RunLayout
      project={project}
      run={run}
      attempt={attempt}
      backend={shown?.backend}
      events={events}
      query={query}
      ended={ended || (shown?.ended_at != null && shown.number === attempt)}
      elapsedMs={
        (run.ended_at ? new Date(run.ended_at).getTime() : now) -
        new Date(run.started_at).getTime()
      }
      usage={attemptsUsage(run.attempts)}
      result={
        hasResult(run) || next !== null ? (
          <>
            <ResultPanel
              run={run}
              commit={mergedCommit(events)}
              next={next}
              onViewNext={onViewNext}
              onOpenTicket={onOpenTicket}
              runNext={runNext}
            />
            {run.ended_at !== null ? (
              <Button size="sm" variant="ghost" onClick={onShowPast}>
                <History aria-hidden />
                Past runs
              </Button>
            ) : null}
          </>
        ) : null
      }
      onOpenTicket={onOpenTicket}
    />
  );
}
