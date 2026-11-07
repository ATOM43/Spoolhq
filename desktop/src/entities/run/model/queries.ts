import { useQuery } from "@tanstack/react-query";

import { api, body, queryKeys, type Schemas } from "@/shared/api";

export type CurrentRun = Schemas["CurrentRun"];

/** The project's active (else latest) run. Kept fresh by run events. */
export function useCurrentRun(project: string) {
  return useQuery({
    queryKey: queryKeys.runs(project),
    queryFn: () =>
      body(
        api.GET("/api/projects/{name}/runs/current", {
          params: { path: { name: project } },
        }),
      ),
    retry: false,
  });
}

export type RunDetail = Schemas["RunDetail"];
export type RunAttempt = Schemas["AttemptView"];

/** One run with its attempts. Under the runs key, so run events refresh it. */
export function useRun(project: string, runId: number | null) {
  return useQuery({
    queryKey: [...queryKeys.runs(project), "detail", runId],
    queryFn: () =>
      body(
        api.GET("/api/projects/{name}/runs/{run_id}", {
          params: { path: { name: project, run_id: runId ?? 0 } },
        }),
      ),
    enabled: runId !== null,
    retry: false,
  });
}
