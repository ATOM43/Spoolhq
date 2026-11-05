import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api, body, queryKeys } from "@/shared/api";

/** Resume a run a stopped daemon interrupted (a new run of the ticket picks up its
 * worktree), or discard it (the worktree goes, the ticket returns to Ready). */
export function useInterruptedRun(project: string, ticket: string) {
  const queryClient = useQueryClient();
  const params = { params: { path: { name: project, ticket_id: ticket } } };
  return useMutation({
    mutationFn: async (what: "resume" | "discard") => {
      await (what === "resume"
        ? body(api.POST("/api/projects/{name}/run/ticket/{ticket_id}", params))
        : body(
            api.POST(
              "/api/projects/{name}/tickets/{ticket_id}/discard",
              params,
            ),
          ));
    },
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.projects }),
  });
}
