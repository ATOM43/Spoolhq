import { useInfiniteQuery } from "@tanstack/react-query";

import { api, body, queryKeys, type Schemas } from "@/shared/api";

export type RunRow = Schemas["RunRow"];

/** The project's ticket runs, newest first, 50 a page. Under the runs key, so a run
 * event refetches the pages already loaded: a run that just ended shows up on top. */
export function useRunHistory(project: string) {
  return useInfiniteQuery({
    queryKey: [...queryKeys.runs(project), "history"],
    queryFn: ({ pageParam }) =>
      body(
        api.GET("/api/projects/{name}/runs", {
          params: {
            path: { name: project },
            query: {
              kind: "ticket",
              limit: 50,
              ...(pageParam === null ? {} : { cursor: pageParam }),
            },
          },
        }),
      ),
    initialPageParam: null as string | null,
    getNextPageParam: (page) => page.next_cursor ?? undefined,
    retry: false,
  });
}
