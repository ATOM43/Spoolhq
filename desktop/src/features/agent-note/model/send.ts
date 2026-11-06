import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api, queryKeys } from "@/shared/api";

export type NoteKind = "unblock" | "changes";

export const NOTE_MAX = 4000;

/** Unblock (`…/unblock`) or request changes (`…/reject`): a new attempt with the note. */
export function useSendNote(project: string, ticketId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      kind,
      note,
      resetRetries,
    }: {
      kind: NoteKind;
      note: string;
      resetRetries: boolean;
    }) => {
      const path = { name: project, ticket_id: ticketId };
      return kind === "unblock"
        ? api.POST("/api/projects/{name}/tickets/{ticket_id}/unblock", {
            params: { path },
            body: { note, reset_retries: resetRetries },
          })
        : api.POST("/api/projects/{name}/tickets/{ticket_id}/reject", {
            params: { path },
            body: { note },
          });
    },
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
