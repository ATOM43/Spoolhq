import { useQuery } from "@tanstack/react-query";

import { api, body, DaemonError, queryKeys, type Schemas } from "@/shared/api";

/** One "Done when" item as the reviewer (or a gate) judged it. */
export interface ItemVerdict {
  text: string;
  met: boolean;
  reason: string;
}

/** A review that stopped early has no verdicts: an older attempt's count instead. */
function verdicts(review: Schemas["ReviewReport"]): ItemVerdict[] | null {
  return review.stopped == null ? review.items : null;
}

async function latestReview(
  project: string,
  runId: number,
): Promise<ItemVerdict[]> {
  const run = await body(
    api.GET("/api/projects/{name}/runs/{run_id}", {
      params: { path: { name: project, run_id: runId } },
    }),
  );
  // Newest attempt first; an attempt that stopped before review has no review file.
  for (const attempt of [...run.attempts].reverse()) {
    try {
      const review = await body(
        api.GET("/api/projects/{name}/runs/{run_id}/attempts/{number}/review", {
          params: {
            path: { name: project, run_id: runId, number: attempt.number },
          },
        }),
      );
      const found = verdicts(review);
      if (found) {
        return found;
      }
    } catch (error) {
      if (!(error instanceof DaemonError && error.detail.kind === "api")) {
        throw error;
      }
    }
  }
  return [];
}

/** The latest review's verdict per "Done when" item, from the ticket's latest run. */
export function useLatestReview(project: string, runId: number | null) {
  return useQuery({
    queryKey: queryKeys.review(project, runId ?? 0),
    queryFn: () => latestReview(project, runId ?? 0),
    enabled: runId !== null,
    retry: false,
  });
}
