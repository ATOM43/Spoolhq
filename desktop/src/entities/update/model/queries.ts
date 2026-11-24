import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getUpdateStatus,
  installUpdate,
  queryKeys,
  type UpdateStatus,
} from "@/shared/api";

/** How often the webview reads Rust's update state (memory only, no request). */
export const UPDATE_POLL_MS = 60_000;

/** The update state Rust keeps; Rust checks the feed at launch and every 6 h. */
export function useUpdateStatus() {
  return useQuery({
    queryKey: queryKeys.update,
    queryFn: () => getUpdateStatus(),
    refetchInterval: UPDATE_POLL_MS,
    retry: false,
  });
}

function useSetStatus() {
  const queryClient = useQueryClient();
  return (status: UpdateStatus) => {
    queryClient.setQueryData(queryKeys.update, status);
  };
}

/** **Check now** (also after the setting changes; with checks off no request is made). */
export function useCheckNow() {
  const setStatus = useSetStatus();
  return useMutation({
    mutationFn: () => getUpdateStatus(true),
    onSuccess: setStatus,
  });
}

/** **Install and restart**; resolves only when it stopped (refused or failed). */
export function useInstallUpdate() {
  const setStatus = useSetStatus();
  return useMutation({ mutationFn: installUpdate, onSuccess: setStatus });
}
