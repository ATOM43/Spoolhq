import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, body, queryKeys, type Schemas } from "@/shared/api";

export type Plan = Schemas["PlanView"];
export type PlanProblem = Schemas["PlanProblemView"];

/** The plan's state, size and problems. Its key sits under the project's tickets, so
 * the run events that refresh the tickets refresh it too. */
export function usePlan(project: string) {
  return useQuery({
    queryKey: queryKeys.plan(project),
    queryFn: () =>
      body(
        api.GET("/api/projects/{name}/plan", {
          params: { path: { name: project } },
        }),
      ),
    retry: false,
  });
}

/** `POST …/plan/generate`; the run events then report the planner's progress. */
export function useGeneratePlan(project: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      body(
        api.POST("/api/projects/{name}/plan/generate", {
          params: { path: { name: project } },
        }),
      ),
    onSettled: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.runs(project) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.projects }),
        queryClient.invalidateQueries({ queryKey: queryKeys.tickets(project) }),
      ]),
  });
}

/** `POST …/plan/approve`: every draft becomes ready (409 `plan_invalid` otherwise). */
export function useApprovePlan(project: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      body(
        api.POST("/api/projects/{name}/plan/approve", {
          params: { path: { name: project } },
        }),
      ),
    onSettled: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.projects }),
        queryClient.invalidateQueries({ queryKey: queryKeys.tickets(project) }),
      ]),
  });
}

/** A problem as the banner links it: "Cycle T07 → T09 → T07", else its message. */
export function problemLabel(problem: PlanProblem): string {
  const ids = problem.ticket_ids;
  return problem.code === "cycle" && ids.length > 0
    ? `Cycle ${[...ids, ids[0]].join(" → ")}`
    : problem.message;
}
