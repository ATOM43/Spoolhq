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

export interface RunLimits {
  gateRetries: number;
  reviewRetries: number;
  /** The first attempt plus both kinds of retries: the most a run takes. */
  maxAttempts: number;
}

/** `limits` from project.yaml (defaults 3 and 2); null until the settings load. */
export function useRunLimits(project: string): RunLimits | null {
  const settings = useQuery({
    queryKey: ["project-settings", project],
    queryFn: () =>
      body(
        api.GET("/api/projects/{name}/settings", {
          params: { path: { name: project } },
        }),
      ),
    retry: false,
    staleTime: 60_000,
  });
  if (!settings.data) {
    return null;
  }
  const limits = settings.data.settings.limits as
    { gate_retries?: unknown; review_retries?: unknown } | undefined;
  const count = (value: unknown, fallback: number) =>
    typeof value === "number" ? value : fallback;
  const gateRetries = count(limits?.gate_retries, 3);
  const reviewRetries = count(limits?.review_retries, 2);
  return {
    gateRetries,
    reviewRetries,
    maxAttempts: 1 + gateRetries + reviewRetries,
  };
}
