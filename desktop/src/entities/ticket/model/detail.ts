import { useQuery } from "@tanstack/react-query";

import { api, queryKeys, type Schemas } from "@/shared/api";

export type TicketDetail = Schemas["TicketDetail"];
export type TicketMeta = Schemas["TicketMeta"];
export type TicketAttempt = Schemas["TicketAttemptView"];
export type RuleHit = Schemas["RuleHitView"];

/** One ticket with its latest run, attempts and git state, and the file's ETag. */
export function useTicketDetail(project: string, id: string) {
  return useQuery({
    // Under the tickets' key, so run events refresh it with the list.
    queryKey: queryKeys.ticket(project, id),
    queryFn: async () => {
      const { data, response } = await api.GET(
        "/api/projects/{name}/tickets/{ticket_id}",
        { params: { path: { name: project, ticket_id: id } } },
      );
      return {
        ticket: data as TicketDetail,
        etag: response.headers.get("ETag") ?? "",
      };
    },
    retry: false,
  });
}

/** `PUT …/tickets/{id}` with `If-Match`; rejects 412 on a conflict, 422 with the field. */
export async function saveTicket(
  project: string,
  id: string,
  meta: TicketMeta,
  body: string,
  etag: string,
): Promise<void> {
  await api.PUT("/api/projects/{name}/tickets/{ticket_id}", {
    params: {
      path: { name: project, ticket_id: id },
      header: { "if-match": etag },
    },
    body: { meta, body },
  });
}

/** A merge-policy rule that fired, as a short chip label. */
export function ruleLabel({ rule, detail }: RuleHit): string {
  switch (rule) {
    case "diff_size":
      return `Diff ${detail}`;
    case "protected_paths":
      return `Touches ${detail}`;
    case "review_required":
      return "Marked review-required";
    case "needs_human":
      return "Reviewer: needs human";
    case "hold_mode":
      return "Hold mode: every ticket waits";
    default:
      return `${rule}: ${detail}`;
  }
}
