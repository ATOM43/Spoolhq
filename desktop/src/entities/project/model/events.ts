import { useQueryClient, type QueryKey } from "@tanstack/react-query";
import { useEffect } from "react";

import { queryKeys, subscribeEvents } from "@/shared/api";

/** Events that can change a project's progress, run state or tickets. */
const PROJECT_EVENT = /^(run\.|integrate$|policy\.decision$)/;
/** Events that change what the current run shows. */
const RUN_EVENT =
  /^(run\.|attempt\.|gate\.result$|review\.verdict$|integrate$|policy\.decision$)/;
/** A burst of events (a replay, a busy run) becomes one refetch per query. */
export const COALESCE_MS = 250;

// The last seq seen per project, so a remount resumes instead of replaying everything.
const lastSeq = new Map<string, number>();

/**
 * Keep the project, ticket and run queries of `names` in step with their live run
 * events: each relevant event invalidates them (coalesced), so nothing polls.
 */
export function useProjectEvents(names: readonly string[]): void {
  const queryClient = useQueryClient();
  const key = names.join("\n");

  useEffect(() => {
    const pending = new Map<string, QueryKey>();
    let timer: ReturnType<typeof setTimeout> | null = null;
    const flush = () => {
      timer = null;
      for (const queryKey of pending.values()) {
        void queryClient.invalidateQueries({ queryKey });
      }
      pending.clear();
    };
    const mark = (...keys: QueryKey[]) => {
      for (const queryKey of keys) {
        pending.set(JSON.stringify(queryKey), queryKey);
      }
      timer ??= setTimeout(flush, COALESCE_MS);
    };

    const stops = (key === "" ? [] : key.split("\n")).map((project) =>
      subscribeEvents(
        { project, since: lastSeq.get(project) ?? 0 },
        (event) => {
          lastSeq.set(project, event.seq);
          if (PROJECT_EVENT.test(event.type)) {
            // ["projects"] covers the list and the project's own detail query.
            mark(queryKeys.projects, queryKeys.tickets(project));
          }
          if (RUN_EVENT.test(event.type)) {
            mark(queryKeys.runs(project));
          }
        },
      ),
    );
    return () => {
      for (const stop of stops) {
        stop();
      }
      if (timer !== null) {
        clearTimeout(timer);
      }
    };
  }, [key, queryClient]);
}
