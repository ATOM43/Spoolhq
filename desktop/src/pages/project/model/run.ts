import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api, queryKeys } from "@/shared/api";

export type RunAction = "next" | "all" | "pause" | "resume" | "cancel";

const PATHS = {
  next: "/api/projects/{name}/run/next",
  all: "/api/projects/{name}/run/all",
  pause: "/api/projects/{name}/run/pause",
  resume: "/api/projects/{name}/run/resume",
  cancel: "/api/projects/{name}/run/cancel",
} as const;

/** Start, pause, resume or cancel the project's run; then refetch what it changes. */
export function useRunAction(project: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (action: RunAction) =>
      api.POST(PATHS[action], { params: { path: { name: project } } }),
    onSettled: () =>
      Promise.all(
        [
          queryKeys.projects,
          queryKeys.runs(project),
          queryKeys.tickets(project),
        ].map((queryKey) => queryClient.invalidateQueries({ queryKey })),
      ),
  });
}
