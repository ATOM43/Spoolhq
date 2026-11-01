import { useQueryClient, type QueryKey } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import { queryKeys, subscribeEvents } from "@/shared/api";

/** Events that can change a project's progress, run state or tickets. */
const PROJECT_EVENT = /^(run\.|integrate$|policy\.decision$)/;
/** Events that change what the current run shows. */
const RUN_EVENT =
  /^(run\.|attempt\.|gate\.result$|review\.verdict$|integrate$|policy\.decision$)/;
/** A burst of events (a replay, a busy run) becomes one refetch per query. */
export const COALESCE_MS = 250;

// The last seq seen per project, so a remount resumes where the last stream stopped.
const lastSeq = new Map<string, number>();

/** A project as its REST answer gave it: `latest_seq` is where its state was read. */
export interface EventSource {
  name: string;
  latest_seq?: number | undefined;
}

/**
 * Keep the project, ticket and run queries of `projects` in step with their live run
 * events: each relevant event invalidates them (coalesced), so nothing polls.
 *
 * The state was loaded over REST first, so the stream starts after that answer's
 * `latest_seq` (or after the last event this app already saw): no history is
 * replayed, and an event written between the REST call and the subscribe still
 * arrives, since the daemon replays everything after `since`.
 */
export function useProjectEvents(projects: readonly EventSource[]): void {
  const queryClient = useQueryClient();
  const key = projects.map((project) => project.name).join("\n");
  // Read when a stream starts; a later REST answer doesn't restart it.
  const startsRef = useRef(new Map<string, number>());
  useEffect(() => {
    // Runs before the effect below, so a new stream sees the latest answer.
    startsRef.current = new Map(
      projects.map((p) => [p.name, p.latest_seq ?? 0]),
    );
  });

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
        {
          project,
          since: Math.max(
            lastSeq.get(project) ?? 0,
            startsRef.current.get(project) ?? 0,
          ),
        },
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
