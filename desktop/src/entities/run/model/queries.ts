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
