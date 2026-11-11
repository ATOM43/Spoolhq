import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  asTyped,
  createTicket,
  joinBody,
  saveTicket,
  splitBody,
  type TicketDetail,
  type TicketMeta,
} from "@/entities/ticket";
import { DaemonError, queryKeys } from "@/shared/api";

export interface Draft {
  title: string;
  scope: string;
  doneWhen: string;
  dependsOn: string[];
  estimate: string;
  reviewRequired: boolean;
}

export type FieldName = keyof Draft | "form";

/** The editable parts of a ticket, as the form shows them. */
export function draftOf(ticket: TicketDetail): Draft {
  const parts = splitBody(ticket.body);
  return {
    title: ticket.meta.title,
    scope: asTyped(parts.scope),
    doneWhen: asTyped(parts.doneWhen),
    dependsOn: [...(ticket.meta.depends_on ?? [])],
    estimate: String(ticket.meta.estimate_h),
    reviewRequired: ticket.meta.review_required,
  };
}

/** The Add ticket form before anything is typed; T41 passes a filled one instead. */
export const EMPTY_DRAFT: Draft = {
  title: "",
  scope: "",
  doneWhen: "",
  dependsOn: [],
  estimate: "1",
  reviewRequired: false,
};

export const sameDraft = (a: Draft, b: Draft) =>
  JSON.stringify(a) === JSON.stringify(b);

/** Why the draft can't be saved yet, or null. */
export function checkDraft(draft: Draft): Partial<Record<FieldName, string>> {
  const errors: Partial<Record<FieldName, string>> = {};
  const hours = Number(draft.estimate);
  if (draft.title.trim() === "") {
    errors.title = "Give the ticket a title";
  }
  if (!(hours >= 0.5 && hours <= 8 && Number.isInteger(hours * 2))) {
    errors.estimate = "Between 0.5 and 8 h, in steps of 0.5";
  }
  return errors;
}

/** The daemon's field name (`meta.depends_on`, `done_when`) as the form's. */
const FIELDS: Record<string, FieldName> = {
  "meta.title": "title",
  "meta.depends_on": "dependsOn",
  "meta.estimate_h": "estimate",
  "meta.review_required": "reviewRequired",
  done_when: "doneWhen",
  body: "scope",
  // A new ticket's fields (`POST …/tickets`).
  title: "title",
  scope: "scope",
  depends_on: "dependsOn",
  estimate_h: "estimate",
  review_required: "reviewRequired",
};

export type SaveError =
  | { kind: "conflict"; etag: string }
  | { kind: "field"; field: FieldName; message: string };

export function saveError(error: unknown): SaveError {
  if (error instanceof DaemonError && error.detail.kind === "api") {
    const { status, etag, field, message } = error.detail;
    if (status === 412 && etag) {
      return { kind: "conflict", etag };
    }
    return { kind: "field", field: FIELDS[field ?? ""] ?? "form", message };
  }
  return {
    kind: "field",
    field: "form",
    message: error instanceof Error ? error.message : String(error),
  };
}

/** Save the draft over the file whose ETag is `etag`, or as a new ticket when there
 * is none yet; refetch the tickets after. Resolves to the ticket's id. */
export function useSaveDraft(project: string, ticket: TicketDetail | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ draft, etag }: { draft: Draft; etag: string }) => {
      if (ticket === null) {
        return createTicket(project, {
          title: draft.title,
          scope: draft.scope,
          done_when: draft.doneWhen,
          depends_on: draft.dependsOn,
          estimate_h: Number(draft.estimate),
          review_required: draft.reviewRequired,
        });
      }
      const meta: TicketMeta = {
        ...ticket.meta,
        title: draft.title,
        depends_on: draft.dependsOn,
        estimate_h: Number(draft.estimate),
        review_required: draft.reviewRequired,
      };
      const body = joinBody(
        splitBody(ticket.body),
        draft.scope,
        draft.doneWhen,
      );
      await saveTicket(project, ticket.id, meta, body, etag);
      return ticket.id;
    },
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.tickets(project) }),
        // A new ticket changes the project's count and what runs next.
        ticket === null
          ? queryClient.invalidateQueries({ queryKey: queryKeys.projects })
          : null,
      ]),
  });
}
