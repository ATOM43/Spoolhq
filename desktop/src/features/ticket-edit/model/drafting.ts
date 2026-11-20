import { useQuery } from "@tanstack/react-query";

import { api, body, DaemonError, queryKeys, type Schemas } from "@/shared/api";

import { FIELDS, type Draft, type FieldName, type Problems } from "./form";

export type DraftJob = Schemas["DraftJobView"];

export const REQUEST_MAX = 2000;

/** One planner draft as the form edits it, with what is still wrong with it. */
export interface Drafted {
  ref: string;
  draft: Draft;
  /** The daemon's problems by form field; each clears when its field is edited. */
  problems: Problems;
  /** Muted lines on the draft's tab: problems on fields the form doesn't show, and
   * dependencies dropped with a removed draft. */
  notes: string[];
  /** Null when the planner's phase had a problem: the daemon then picks it. */
  phase: number | null;
}

/** Start drafting from `request`; resolves to the job's id, or rejects with the
 * daemon's refusal (409, a message to show as is). */
export async function startDraft(project: string, request: string) {
  const started = await body(
    api.POST("/api/projects/{name}/tickets/draft", {
      params: { path: { name: project } },
      body: { request },
    }),
  );
  return started.job_id;
}

export async function cancelDraft(project: string, jobId: string) {
  await api.POST("/api/projects/{name}/tickets/draft/{job_id}/cancel", {
    params: { path: { name: project, job_id: jobId } },
  });
}

/** The draft job, read every 500 ms while it runs; nothing once it ended or the form
 * that asked is gone (the query then has no observer). */
export function useDraftJob(project: string, jobId: string | null) {
  return useQuery({
    queryKey: queryKeys.draftJob(project, jobId ?? ""),
    queryFn: () =>
      body(
        api.GET("/api/projects/{name}/tickets/draft/{job_id}", {
          params: { path: { name: project, job_id: jobId ?? "" } },
        }),
      ),
    enabled: jobId !== null,
    retry: false,
    refetchInterval: (query) =>
      query.state.data?.state === "running" ? 500 : false,
  });
}

/** A succeeded job's drafts, in ref order, as the form's values. */
export function draftsOf(job: DraftJob): Drafted[] {
  return job.drafts.map((view) => {
    const problems: Problems = {};
    const notes: string[] = [];
    let phase: number | null = view.phase;
    for (const problem of view.problems) {
      const field = FIELDS[problem.field];
      if (field === undefined || field === "form") {
        // The form can't edit it, so it mustn't block saving: say what was left out.
        notes.push(`Left out: ${problem.message}`);
        if (problem.field === "phase") {
          phase = null;
        }
      } else {
        const before = problems[field];
        problems[field] = before
          ? `${before}; ${problem.message}`
          : problem.message;
      }
    }
    return {
      ref: view.ref,
      draft: {
        title: view.title,
        scope: view.scope,
        doneWhen: view.done_when.map((item) => `- [ ] ${item}`).join("\n"),
        dependsOn: [...view.depends_on],
        estimate: String(view.estimate_h),
        reviewRequired: view.review_required,
      },
      problems,
      notes,
      phase,
    };
  });
}

/** The drafts without `ref`; any other draft that depended on it no longer does, and
 * says so on its tab. */
export function withoutDraft(drafts: Drafted[], ref: string): Drafted[] {
  return drafts
    .filter((drafted) => drafted.ref !== ref)
    .map((drafted) =>
      drafted.draft.dependsOn.includes(ref)
        ? {
            ...drafted,
            draft: {
              ...drafted.draft,
              dependsOn: drafted.draft.dependsOn.filter((dep) => dep !== ref),
            },
            notes: [
              ...drafted.notes,
              `${ref} was removed, so this no longer depends on it.`,
            ],
          }
        : drafted,
    );
}

/** Save the drafts together (all or none); resolves to the new ids in order. */
export async function saveDrafts(project: string, drafts: Drafted[]) {
  const saved = await body(
    api.POST("/api/projects/{name}/tickets/batch", {
      params: { path: { name: project } },
      body: {
        tickets: drafts.map(({ ref, draft, phase }) => ({
          ref,
          title: draft.title,
          scope: draft.scope,
          done_when: draft.doneWhen,
          depends_on: draft.dependsOn,
          estimate_h: Number(draft.estimate),
          review_required: draft.reviewRequired,
          phase,
        })),
      },
    }),
  );
  return saved.tickets.map((ticket) => ticket.id);
}

/** A batch refusal on its draft and field (`tickets.1.depends_on`), or for the form. */
export function batchError(error: unknown): {
  index: number | null;
  field: FieldName;
  message: string;
} {
  if (error instanceof DaemonError && error.detail.kind === "api") {
    const { field, message } = error.detail;
    const match = /^tickets\.(\d+)\.(\w+)/.exec(field ?? "");
    if (match) {
      return {
        index: Number(match[1]),
        field: FIELDS[match[2] ?? ""] ?? "form",
        message,
      };
    }
    return { index: null, field: "form", message };
  }
  const message = error instanceof Error ? error.message : String(error);
  return { index: null, field: "form", message };
}
