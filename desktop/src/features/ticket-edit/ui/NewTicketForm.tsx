import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";

import type { Ticket } from "@/entities/ticket";
import { queryKeys } from "@/shared/api";

import {
  cancelDraft,
  draftsOf,
  startDraft,
  useDraftJob,
  type Drafted,
} from "../model/drafting";
import type { Draft } from "../model/form";
import { DescribeIt } from "./DescribeIt";
import { DraftTabs } from "./DraftTabs";
import { TicketEditForm } from "./TicketEditForm";

/**
 * The Add ticket form: written by hand as before, or drafted by the planner from a few
 * lines (Describe it). Drafts open in the form unsaved; see {@link DraftTabs}.
 */
export function NewTicketForm({
  project,
  draft,
  others,
  blocker,
  blockerAction,
  onSaved,
  onClose,
  onDirtyChange,
  onDraftingChange,
}: {
  project: string;
  /** What the hand-written form starts with; default: empty. */
  draft?: Draft | undefined;
  others: readonly Ticket[];
  /** Why the daemon would refuse to draft, or null. */
  blocker: string | null;
  blockerAction?: ReactNode;
  onSaved: (id: string) => void;
  onClose: () => void;
  onDirtyChange: (dirty: boolean) => void;
  /** The running draft job's id, or null: closing then asks and cancels it. */
  onDraftingChange: (jobId: string | null) => void;
}) {
  const queryClient = useQueryClient();
  const [request, setRequest] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Drafted[] | null>(null);
  const [split, setSplit] = useState(false);
  const [handDirty, setHandDirty] = useState(false);
  const job = useDraftJob(project, jobId);

  const start = useMutation({
    mutationFn: () => startDraft(project, request),
    onMutate: () => {
      setFailure(null);
    },
    onSuccess: setJobId,
    onError: (error) => {
      setFailure(error.message);
    },
  });
  const cancel = useMutation({
    mutationFn: (id: string) => cancelDraft(project, id),
    onSettled: (_data, _error, id) =>
      queryClient.invalidateQueries({
        queryKey: queryKeys.draftJob(project, id),
      }),
  });

  // The job ended: its drafts open in the form, or its message shows. Handled while
  // rendering (not in an effect) so the form never shows a finished job as running.
  const ended = job.data && job.data.state !== "running" ? job.data : null;
  if (jobId !== null && (ended !== null || job.isError)) {
    setJobId(null);
    if (ended?.state === "succeeded") {
      const opened = draftsOf(ended);
      setDrafts(opened);
      setSplit(opened.length > 1);
    } else if (ended?.state === "failed") {
      setFailure(ended.error ?? "The planner couldn't draft this");
    } else if (job.isError) {
      setFailure(job.error.message);
    }
  }

  const drafting = jobId !== null;
  useEffect(() => {
    onDraftingChange(jobId);
  }, [jobId, onDraftingChange]);
  useEffect(() => {
    onDirtyChange(drafts !== null || handDirty || request.trim() !== "");
  }, [drafts, handDirty, request, onDirtyChange]);

  if (drafts !== null) {
    return (
      <DraftTabs
        project={project}
        others={others}
        drafts={drafts}
        split={split}
        onDraftsChange={setDrafts}
        onDiscard={() => {
          setDrafts(null);
        }}
        onSaved={onSaved}
        onClose={onClose}
      />
    );
  }
  return (
    <>
      {/* Only on the empty form, so a draft never overwrites what was typed. */}
      {handDirty ? null : (
        <DescribeIt
          request={request}
          onRequestChange={setRequest}
          blocker={blocker}
          blockerAction={blockerAction}
          starting={start.isPending}
          drafting={drafting}
          cancelling={cancel.isPending}
          failure={failure}
          onDraft={() => {
            start.mutate();
          }}
          onCancel={() => {
            if (jobId !== null) {
              cancel.mutate(jobId);
            }
          }}
        />
      )}
      {drafting ? null : (
        <TicketEditForm
          project={project}
          ticket={null}
          draft={draft}
          others={others}
          onDone={(saved) => {
            if (saved) {
              onSaved(saved);
            } else {
              onClose();
            }
          }}
          onDirtyChange={setHandDirty}
        />
      )}
    </>
  );
}
