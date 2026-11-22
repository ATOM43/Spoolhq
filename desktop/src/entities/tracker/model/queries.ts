import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import { api, body, queryKeys, type Schemas } from "@/shared/api";

export type TrackerView = Schemas["TrackerView"];

/** Sync runs outside ticket runs, so no run event carries it: the state is polled. */
export const TRACKER_POLL_MS = 15_000;

const LABELS: Record<string, string> = { clickup: "ClickUp" };

/** "ClickUp" for `clickup`; an unknown kind shows as it is. */
export const trackerLabel = (kind: string): string => LABELS[kind] ?? kind;

/** A project's sync state. Refetched every 15 s while on screen, and only for a
 * project with a tracker: without one the first answer (`kind: null`) stops it. */
export function trackerQuery(project: string) {
  return queryOptions({
    queryKey: queryKeys.tracker(project),
    queryFn: () =>
      body(
        api.GET("/api/projects/{name}/tracker", {
          params: { path: { name: project } },
        }),
      ),
    retry: false,
    refetchInterval: (query) =>
      query.state.data?.kind ? TRACKER_POLL_MS : false,
  });
}

/** Push now (queue every ticket) or Retry (re-queue what failed); the state is
 * refetched right after either. */
export function useTrackerAction(project: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (action: "push" | "retry") => {
      const params = { params: { path: { name: project } } };
      await body(
        action === "push"
          ? api.POST("/api/projects/{name}/tracker/push", params)
          : api.POST("/api/projects/{name}/tracker/retry", params),
      );
    },
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.tracker(project) }),
  });
}
