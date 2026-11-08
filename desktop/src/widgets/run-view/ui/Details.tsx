import { LoaderCircle } from "lucide-react";
import { useState, type ReactNode } from "react";

import { useArtifact } from "@/entities/run";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/ui";

import { NO_EVENTS, type LiveDetails } from "../model/details";
import { DiffPanel } from "./DiffPanel";
import { Failed } from "./Failed";
import { GatesPanel } from "./GatesPanel";
import { ReviewPanel } from "./ReviewPanel";

export type DetailsTab = "gates" | "review" | "diff";

export interface DetailsProps {
  project: string;
  runId: number;
  /** The attempt in view; null before the run's first. */
  attempt: number | null;
  live: LiveDetails;
  /** The attempt is over: "before" states say the step never ran instead. */
  ended: boolean;
  diff: ReturnType<typeof useArtifact<"diff">>;
  tab: DetailsTab;
  onTab: (tab: DetailsTab) => void;
  file: string | null;
  onFile: (path: string) => void;
}

/** The right-hand panel: the attempt's Gates, Review and Diff, each with its loading,
 * error and "not yet" state. */
export function Details(props: DetailsProps) {
  const { project, runId, attempt, live, ended, diff, tab } = props;
  const gates = useArtifact(
    "gates",
    project,
    runId,
    attempt,
    live.stamps.gates,
  );
  const review = useArtifact(
    "review",
    project,
    runId,
    attempt,
    live.stamps.review,
  );
  const files = diff.data?.files.length;
  return (
    <section
      aria-label="Details"
      className="flex min-h-0 basis-2/5 flex-col p-4"
    >
      <Tabs
        value={tab}
        onValueChange={(value) => {
          props.onTab(value as DetailsTab);
        }}
        className="min-h-0 flex-1 gap-3"
      >
        <TabsList>
          <TabsTrigger value="gates">Gates</TabsTrigger>
          <TabsTrigger value="review">Review</TabsTrigger>
          <TabsTrigger value="diff">
            Diff
            {files ? (
              <span className="text-xs text-ink-muted">
                {files} {files === 1 ? "file" : "files"}
              </span>
            ) : null}
          </TabsTrigger>
        </TabsList>
        <TabsContent value="gates" className="min-h-0 overflow-auto">
          <Loaded what="the gates" query={gates} attempt={attempt}>
            <GatesPanel report={gates.data ?? null} live={live} ended={ended} />
          </Loaded>
        </TabsContent>
        <TabsContent value="review" className="min-h-0 overflow-auto">
          <Loaded what="the review" query={review} attempt={attempt}>
            <ReviewPanel
              report={review.data ?? null}
              reviewing={live.reviewing}
              ended={ended}
            />
          </Loaded>
        </TabsContent>
        <TabsContent value="diff" className="min-h-0 overflow-auto">
          <Loaded what="the diff" query={diff} attempt={attempt}>
            <DiffPanel
              report={diff.data ?? null}
              ended={ended}
              selected={props.file}
              onSelect={props.onFile}
            />
          </Loaded>
        </TabsContent>
      </Tabs>
    </section>
  );
}

function Loaded({
  what,
  query,
  attempt,
  children,
}: {
  what: string;
  query: {
    isPending: boolean;
    isError: boolean;
    error: Error | null;
    refetch: () => unknown;
  };
  attempt: number | null;
  children: ReactNode;
}) {
  if (attempt === null) {
    return (
      <p className="py-2 text-sm text-ink-muted">
        The details appear once the first attempt starts.
      </p>
    );
  }
  if (query.isError) {
    return (
      <Failed
        what={what}
        message={query.error?.message ?? ""}
        onRetry={() => void query.refetch()}
      />
    );
  }
  if (query.isPending) {
    return (
      <p className="flex items-center gap-2 py-2 text-sm text-ink-muted">
        <LoaderCircle aria-hidden className="size-4 motion-safe:animate-spin" />
        Loading {what}…
      </p>
    );
  }
  return children;
}

/** A finished attempt's details (`?attempt=N`): no events, each report loaded once. */
export function AttemptDetails({
  project,
  runId,
  attempt,
}: {
  project: string;
  runId: number;
  attempt: number;
}) {
  const [tab, setTab] = useState<DetailsTab>("gates");
  const [file, setFile] = useState<string | null>(null);
  const diff = useArtifact("diff", project, runId, attempt);
  return (
    <Details
      project={project}
      runId={runId}
      attempt={attempt}
      live={NO_EVENTS}
      ended
      diff={diff}
      tab={tab}
      onTab={setTab}
      file={file}
      onFile={setFile}
    />
  );
}
