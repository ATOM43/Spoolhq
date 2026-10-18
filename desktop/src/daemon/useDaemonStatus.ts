import { useQuery, useQueryClient } from "@tanstack/react-query";

import {
  checkDaemon,
  deriveStatus,
  POLL_INTERVAL_MS,
  type DaemonCheck,
  type DaemonStatus,
} from "./status";

export const DAEMON_STATUS_KEY = ["daemon", "status"] as const;

export interface DaemonStatusResult {
  status: DaemonStatus;
  /** True while a check is in flight. */
  checking: boolean;
  /** Check again now instead of waiting for the next poll. */
  retry: () => void;
}

/** The daemon's status, checked every 3 s. All callers share one poll. */
export function useDaemonStatus(): DaemonStatusResult {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: DAEMON_STATUS_KEY,
    // checkDaemon never throws; failures are part of the result.
    queryFn: () =>
      checkDaemon(queryClient.getQueryData<DaemonCheck>(DAEMON_STATUS_KEY)),
    refetchInterval: POLL_INTERVAL_MS,
    refetchIntervalInBackground: true,
    retry: false,
  });
  return {
    status: deriveStatus(query.data),
    checking: query.isFetching,
    retry: () => {
      void query.refetch();
    },
  };
}
