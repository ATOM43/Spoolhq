import { useQuery } from "@tanstack/react-query";

import { api, body, queryKeys, type Schemas } from "@/shared/api";

export type Ticket = Schemas["TicketView"];
export type TicketStatus = Ticket["meta"]["status"];

/** A project's tickets (and the files that don't load), for `useQuery` or `useQueries`. */
export function ticketsQuery(project: string) {
  return {
    queryKey: queryKeys.tickets(project),
    queryFn: () =>
      body(
        api.GET("/api/projects/{name}/tickets", {
          params: { path: { name: project } },
        }),
      ),
    retry: false,
  } as const;
}

export function useTickets(project: string, { enabled = true } = {}) {
  return useQuery({ ...ticketsQuery(project), enabled });
}
