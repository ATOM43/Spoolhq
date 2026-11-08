import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { api, body, DaemonError, type Schemas } from "@/shared/api";

export type GatesReport = Schemas["GatesReport"];
export type GateReport = Schemas["GateReport"];
export type ReviewReport = Schemas["ReviewReport"];
export type DiffReport = Schemas["DiffReport"];
export type DiffFile = Schemas["DiffFile"];

type Artifact = "gates" | "review" | "diff";
type Report<A extends Artifact> = {
  gates: GatesReport;
  review: ReviewReport;
  diff: DiffReport;
}[A];

const PATHS = {
  gates: "/api/projects/{name}/runs/{run_id}/attempts/{number}/gates",
  review: "/api/projects/{name}/runs/{run_id}/attempts/{number}/review",
  diff: "/api/projects/{name}/runs/{run_id}/attempts/{number}/diff",
} as const;

/** null while the step hasn't written it (404 `not_ready`). */
async function load<A extends Artifact>(
  artifact: A,
  project: string,
  runId: number,
  attempt: number,
): Promise<Report<A> | null> {
  try {
    // One path type for the call: the three share their parameters.
    const path = PATHS[artifact] as (typeof PATHS)["gates"];
    const report: unknown = await body(
      api.GET(path, {
        params: { path: { name: project, run_id: runId, number: attempt } },
      }),
    );
    return report as Report<A>;
  } catch (error) {
    if (
      error instanceof DaemonError &&
      error.detail.kind === "api" &&
      error.detail.code === "not_ready"
    ) {
      return null;
    }
    throw error;
  }
}

/**
 * One attempt's gates, review or diff report; null before its step wrote it. `stamp`
 * is the `seq` of the event that last changed it (its step ending), so a new one
 * fetches again: live updates come from events, never polling. The previous report
 * stays on screen while the next loads.
 */
export function useArtifact<A extends Artifact>(
  artifact: A,
  project: string,
  runId: number | null,
  attempt: number | null,
  stamp = 0,
) {
  return useQuery({
    queryKey: ["run-artifact", project, runId, attempt, artifact, stamp],
    queryFn: () => load(artifact, project, runId ?? 0, attempt ?? 0),
    enabled: runId !== null && attempt !== null,
    placeholderData: keepPreviousData,
    staleTime: Infinity,
    retry: false,
  });
}
