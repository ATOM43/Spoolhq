import { useMutation, useQueryClient } from "@tanstack/react-query";
import { TriangleAlert, X } from "lucide-react";
import { useState } from "react";

import type { Ticket } from "@/entities/ticket";
import { queryKeys } from "@/shared/api";
import { cn } from "@/shared/lib";
import { Button, ConfirmDialog, ReasonButton, showToast } from "@/shared/ui";

import {
  batchError,
  saveDrafts,
  withoutDraft,
  type Drafted,
} from "../model/drafting";
import { fixFirst, problemCount } from "../model/form";
import { TicketEditForm } from "./TicketEditForm";

/**
 * The planner's drafts in the form, unsaved. One draft is the normal Add ticket form
 * with its own Save; a split shows D1 to D3 as tabs, each the edit form, saved together
 * with **Save all**. A tab with problems shows a marker; Save waits until all are clear.
 */
export function DraftTabs({
  project,
  others,
  drafts,
  split,
  onDraftsChange,
  onDiscard,
  onSaved,
  onClose,
}: {
  project: string;
  others: readonly Ticket[];
  drafts: Drafted[];
  /** The planner answered with more than one draft: tabs, even if one is left. */
  split: boolean;
  onDraftsChange: (drafts: Drafted[]) => void;
  onDiscard: () => void;
  onSaved: (id: string) => void;
  onClose: () => void;
}) {
  const [active, setActive] = useState(drafts[0]?.ref ?? "");
  const [removing, setRemoving] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const save = useMutation({
    mutationFn: () => saveDrafts(project, drafts),
    onSuccess: async (ids) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.tickets(project) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.projects }),
      ]);
      showToast(`Added ${ids.join(", ")}`);
      const first = ids[0];
      if (first) {
        onSaved(first);
      }
    },
    onError: (error) => {
      const { index, field, message } = batchError(error);
      const target = index === null ? undefined : drafts[index];
      if (target === undefined) {
        setFormError(message);
        return;
      }
      update(target.ref, (d) => ({
        ...d,
        problems: { ...d.problems, [field]: message },
      }));
      setActive(target.ref);
    },
  });
  const update = (ref: string, change: (drafted: Drafted) => Drafted) => {
    onDraftsChange(drafts.map((d) => (d.ref === ref ? change(d) : d)));
  };
  const current = drafts.find((d) => d.ref === active) ?? drafts[0];
  if (current === undefined) {
    return null;
  }
  const count = (d: Drafted) => problemCount(d.draft, d.problems);
  const left = drafts.reduce((sum, d) => sum + count(d), 0);
  const form = (
    <>
      {current.notes.map((note) => (
        <p key={note} className="text-sm text-ink-muted">
          {note}
        </p>
      ))}
      <TicketEditForm
        key={current.ref}
        project={project}
        ticket={null}
        others={others}
        refs={drafts
          .filter((d) => d.ref !== current.ref)
          .map((d) => ({ id: d.ref, title: d.draft.title }))}
        value={current.draft}
        drafted={current.problems}
        batch={split}
        onChange={(draft, field) => {
          const problems = { ...current.problems };
          // eslint-disable-next-line @typescript-eslint/no-dynamic-delete -- clears only the edited field
          delete problems[field];
          update(current.ref, (d) => ({ ...d, draft, problems }));
        }}
        onDone={(saved) => {
          if (saved) {
            onSaved(saved);
          } else {
            onClose();
          }
        }}
        onDirtyChange={() => undefined}
      />
    </>
  );

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2 text-sm text-ink-muted">
        <span className="flex-1">
          {split
            ? `The planner split this into ${String(drafts.length)} tickets`
            : "Drafted by the planner; check it before saving."}
        </span>
        <Button type="button" variant="outline" size="sm" onClick={onDiscard}>
          Discard
        </Button>
      </div>
      {split ? (
        <>
          <div
            role="tablist"
            aria-label="Drafts"
            className="flex gap-1 border-b"
          >
            {drafts.map((d) => {
              const problems = count(d);
              return (
                <div
                  key={d.ref}
                  className={cn(
                    "flex items-center rounded-t-md border border-b-0 px-1",
                    d.ref === current.ref
                      ? "bg-surface text-ink"
                      : "bg-surface-sunken text-ink-muted",
                  )}
                >
                  <button
                    type="button"
                    role="tab"
                    aria-selected={d.ref === current.ref}
                    aria-label={
                      problems > 0
                        ? `${d.ref}, ${String(problems)} ${problems === 1 ? "problem" : "problems"}`
                        : d.ref
                    }
                    className="flex items-center gap-1.5 px-2 py-1 text-sm font-medium"
                    onClick={() => {
                      setActive(d.ref);
                    }}
                  >
                    {d.ref}
                    {problems > 0 ? (
                      <span className="flex items-center gap-0.5 text-danger">
                        <TriangleAlert aria-hidden className="size-3.5" />
                        <span>{problems}</span>
                      </span>
                    ) : null}
                  </button>
                  {drafts.length > 1 ? (
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="size-6"
                      aria-label={`Remove ${d.ref}`}
                      onClick={() => {
                        setRemoving(d.ref);
                      }}
                    >
                      <X aria-hidden className="size-3.5" />
                    </Button>
                  ) : null}
                </div>
              );
            })}
          </div>
          <div role="tabpanel" aria-label={current.ref}>
            {form}
          </div>
          {formError ? (
            <p role="alert" className="text-sm text-danger">
              {formError}
            </p>
          ) : null}
          <div className="sticky bottom-0 flex justify-end gap-2 border-t bg-surface py-3">
            <ReasonButton
              type="button"
              reason={
                save.isPending
                  ? "Waiting for the daemon to answer"
                  : left > 0
                    ? fixFirst(left)
                    : null
              }
              onClick={() => {
                setFormError(null);
                save.mutate();
              }}
            >
              Save all
            </ReasonButton>
          </div>
        </>
      ) : (
        form
      )}
      <ConfirmDialog
        open={removing !== null}
        title={`Remove ${removing ?? ""}?`}
        consequence="This draft isn't saved and will be lost; the other drafts stop depending on it."
        action="Remove draft"
        destructive
        onCancel={() => {
          setRemoving(null);
        }}
        onConfirm={() => {
          const rest = withoutDraft(drafts, removing ?? "");
          setRemoving(null);
          if (removing === current.ref) {
            setActive(rest[0]?.ref ?? "");
          }
          onDraftsChange(rest);
        }}
      />
    </div>
  );
}
