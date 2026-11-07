import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

import { api, body, subscribeEvents, type EventEnvelope } from "@/shared/api";

export type RunEvent = EventEnvelope;

/** Not under ["runs", project]: run events invalidate that key, and these are kept
 * current by the stream instead of refetching every page. */
export const runEventsKey = (
  project: string,
  runId: number,
  attempt: number | null,
) => ["run-events", project, runId, attempt ?? 0] as const;

/** `list` with `incoming` added: one event per `seq`, in `seq` order. */
export function mergeEvents(
  list: readonly RunEvent[],
  incoming: readonly RunEvent[],
): RunEvent[] {
  let merged = list as RunEvent[];
  for (const event of incoming) {
    const last = merged.at(-1);
    if (last === undefined || event.seq > last.seq) {
      merged = [...merged, event];
    } else if (!merged.some((seen) => seen.seq === event.seq)) {
      merged = [...merged, event].sort((a, b) => a.seq - b.seq);
    }
  }
  return merged;
}

/** Every stored event of one attempt (its window, see the daemon route), all pages;
 * with no attempt yet (the worktree step), the run's events. */
async function loadAttempt(
  project: string,
  runId: number,
  attempt: number | null,
): Promise<RunEvent[]> {
  let events: RunEvent[] = [];
  let after = 0;
  for (;;) {
    const page = await body(
      api.GET("/api/projects/{name}/runs/{run_id}/events", {
        params: {
          path: { name: project, run_id: runId },
          query: {
            ...(attempt === null ? {} : { attempt }),
            after,
            limit: 2000,
          },
        },
      }),
    );
    events = mergeEvents(events, page.items);
    if (page.next_after == null) {
      return events;
    }
    after = page.next_after;
  }
}

/**
 * One run as it happens: the events of `startAttempt` loaded from its start, then the
 * live stream from the last `seq` loaded (or `since` when the attempt had none yet), so
 * the seam has no gap; a replayed duplicate is dropped by `mergeEvents`. Each event goes
 * to its attempt's cache entry (run-level ones to the newest attempt), and the view
 * moves to a new attempt as soon as it starts. `live` false loads without streaming.
 */
export function useRunEvents({
  project,
  runId,
  startAttempt,
  since,
  live,
}: {
  project: string;
  runId: number;
  /** The run's newest attempt when the view opens; null before its first. */
  startAttempt: number | null;
  since: number;
  live: boolean;
}) {
  const queryClient = useQueryClient();
  const [attempt, setAttempt] = useState(startAttempt);
  if (startAttempt !== null && (attempt === null || startAttempt > attempt)) {
    setAttempt(startAttempt); // the run detail saw a newer attempt first
  }
  const query = useQuery({
    queryKey: runEventsKey(project, runId, attempt),
    queryFn: () => loadAttempt(project, runId, attempt),
    staleTime: Infinity,
    retry: false,
  });
  const loaded = query.isSuccess;
  // Read by the stream's callback, so a new attempt or REST answer never restarts it.
  const newest = useRef(attempt);
  const sinceRef = useRef(since);
  useEffect(() => {
    if (attempt !== null && (newest.current ?? 0) < attempt) {
      newest.current = attempt;
    }
    sinceRef.current = since;
  });

  useEffect(() => {
    if (!live || !loaded) {
      return;
    }
    // From the last event loaded, so the seam with the stream has no gap.
    const cached = queryClient.getQueryData<RunEvent[]>(
      runEventsKey(project, runId, newest.current),
    );
    const from = Math.max(sinceRef.current, cached?.at(-1)?.seq ?? 0);
    return subscribeEvents({ project, since: from }, (event) => {
      if (event.run_id !== runId) {
        return;
      }
      if (
        event.type === "attempt.started" &&
        event.attempt !== null &&
        event.attempt > (newest.current ?? 0)
      ) {
        newest.current = event.attempt;
        setAttempt(event.attempt);
      }
      const key = runEventsKey(project, runId, event.attempt ?? newest.current);
      queryClient.setQueryData<RunEvent[]>(key, (list) =>
        mergeEvents(list ?? [], [event]),
      );
    });
    // Started once per run: the stream reconnects itself with `since`.
  }, [live, loaded, project, runId, queryClient]);

  return { attempt, events: query.data ?? [], query };
}
