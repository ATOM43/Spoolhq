import { TriangleAlert } from "lucide-react";
import { useEffect, useId, useState, type ReactNode } from "react";

import type { Ticket, TicketDetail } from "@/entities/ticket";
import {
  Button,
  ConfirmDialog,
  describedBy,
  Field,
  Input,
  ReasonButton,
  Textarea,
} from "@/shared/ui";

import {
  checkDraft,
  draftOf,
  sameDraft,
  saveError,
  useSaveDraft,
  type Draft,
  type FieldName,
  type SaveError,
} from "../model/form";

/**
 * The drawer in edit mode: title, Scope and "Done when" as markdown, dependencies,
 * estimate and review required, with Save and Cancel at the bottom. Saves with the
 * file's ETag; a 412 shows "Changed on disk · Reload · Keep mine", a 422 its field.
 */
export function TicketEditForm({
  project,
  ticket,
  etag,
  others,
  onDone,
  onReload,
  onDirtyChange,
}: {
  project: string;
  ticket: TicketDetail;
  /** The ETag of the file `ticket` was read from. */
  etag: string;
  /** The project's other tickets, for the dependency picker. */
  others: readonly Ticket[];
  /** Leave edit mode (saved, or cancelled). */
  onDone: () => void;
  /** Read the ticket from disk again (this form is then remounted). */
  onReload: () => void;
  onDirtyChange: (dirty: boolean) => void;
}) {
  const id = useId();
  const [initial] = useState(() => draftOf(ticket));
  const [draft, setDraft] = useState(initial);
  const [error, setError] = useState<SaveError | null>(null);
  const [confirmCancel, setConfirmCancel] = useState(false);
  const save = useSaveDraft(project, ticket);
  const dirty = !sameDraft(draft, initial);
  useEffect(() => {
    onDirtyChange(dirty);
  }, [dirty, onDirtyChange]);

  const problems = checkDraft(draft);
  const fieldError = (name: FieldName) =>
    problems[name] ??
    (error?.kind === "field" && error.field === name ? error.message : null);
  const set = <K extends keyof Draft>(key: K, value: Draft[K]) => {
    setDraft((previous) => ({ ...previous, [key]: value }));
    if (error?.kind === "field" && error.field === key) {
      setError(null);
    }
  };
  const submit = (over: string) => {
    save.mutate(
      { draft, etag: over },
      {
        onSuccess: () => {
          setError(null);
          onDirtyChange(false);
          onDone();
        },
        onError: (failure) => {
          setError(saveError(failure));
        },
      },
    );
  };
  const reason = save.isPending
    ? "Waiting for the daemon to answer"
    : Object.keys(problems).length > 0
      ? "Fix the fields marked in red first"
      : !dirty
        ? "Nothing changed yet"
        : error?.kind === "conflict"
          ? "Reload or keep yours first"
          : null;

  return (
    <>
      <form
        aria-label={`Edit ${ticket.id}`}
        className="flex flex-col gap-4"
        onSubmit={(event) => {
          event.preventDefault();
          if (reason === null) {
            submit(etag);
          }
        }}
      >
        {error?.kind === "conflict" ? (
          <div
            role="alert"
            className="flex flex-wrap items-center gap-2 rounded-md border border-warning bg-surface-sunken px-3 py-2 text-sm"
          >
            <TriangleAlert aria-hidden className="size-4 text-warning" />
            <span>Changed on disk</span>·
            <Button
              type="button"
              variant="link"
              size="sm"
              className="px-0"
              onClick={onReload}
            >
              Reload
            </Button>
            ·
            <Button
              type="button"
              variant="link"
              size="sm"
              className="px-0"
              onClick={() => {
                submit(error.etag);
              }}
            >
              Keep mine
            </Button>
          </div>
        ) : null}
        <Field id={`${id}-title`} label="Title" error={fieldError("title")}>
          <Input
            id={`${id}-title`}
            value={draft.title}
            aria-invalid={!!fieldError("title")}
            aria-describedby={describedBy(`${id}-title`)}
            onChange={(event) => {
              set("title", event.target.value);
            }}
          />
        </Field>
        <Markdown
          id={`${id}-scope`}
          label="Scope"
          value={draft.scope}
          error={fieldError("scope")}
          onChange={(value) => {
            set("scope", value);
          }}
        />
        <Markdown
          id={`${id}-done`}
          label="Done when"
          hint="One “- [ ] …” line per item the reviewer checks."
          value={draft.doneWhen}
          error={fieldError("doneWhen")}
          onChange={(value) => {
            set("doneWhen", value);
          }}
        />
        <fieldset
          className="flex flex-col gap-1.5"
          aria-describedby={describedBy(`${id}-deps`)}
        >
          <legend className="mb-1.5 text-sm font-medium">Depends on</legend>
          {others.length === 0 ? (
            <p className="text-sm text-ink-muted">No other tickets.</p>
          ) : (
            <ul className="flex max-h-40 flex-col gap-1 overflow-auto rounded-md border p-2">
              {others.map((other) => (
                <li key={other.id}>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={draft.dependsOn.includes(other.id)}
                      onChange={(event) => {
                        set(
                          "dependsOn",
                          event.target.checked
                            ? [...draft.dependsOn, other.id]
                            : draft.dependsOn.filter((dep) => dep !== other.id),
                        );
                      }}
                    />
                    <span className="font-mono text-xs">{other.id}</span>
                    <span className="truncate">{other.meta.title}</span>
                  </label>
                </li>
              ))}
            </ul>
          )}
          <FieldError id={`${id}-deps`}>{fieldError("dependsOn")}</FieldError>
        </fieldset>
        <div className="flex flex-wrap items-start gap-6">
          <Field
            id={`${id}-estimate`}
            label="Estimate (h)"
            error={fieldError("estimate")}
          >
            <Input
              id={`${id}-estimate`}
              type="number"
              min={0.5}
              max={8}
              step={0.5}
              className="w-28"
              value={draft.estimate}
              aria-invalid={!!fieldError("estimate")}
              aria-describedby={describedBy(`${id}-estimate`)}
              onChange={(event) => {
                set("estimate", event.target.value);
              }}
            />
          </Field>
          <label className="flex items-center gap-2 pt-7 text-sm">
            <input
              type="checkbox"
              checked={draft.reviewRequired}
              onChange={(event) => {
                set("reviewRequired", event.target.checked);
              }}
            />
            Review required
          </label>
        </div>
        <FieldError id={`${id}-form`}>{fieldError("form")}</FieldError>
        <div className="sticky bottom-0 flex justify-end gap-2 border-t bg-surface py-3">
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              if (dirty) {
                setConfirmCancel(true);
              } else {
                onDone();
              }
            }}
          >
            Cancel
          </Button>
          <ReasonButton type="submit" reason={reason}>
            Save
          </ReasonButton>
        </div>
      </form>
      <ConfirmDialog
        open={confirmCancel}
        title="Discard your changes?"
        consequence={`Your edits to ${ticket.id} aren't saved and will be lost.`}
        action="Discard changes"
        destructive
        onCancel={() => {
          setConfirmCancel(false);
        }}
        onConfirm={() => {
          setConfirmCancel(false);
          onDirtyChange(false);
          onDone();
        }}
      />
    </>
  );
}

function Markdown({
  id,
  label,
  hint,
  value,
  error,
  onChange,
}: {
  id: string;
  label: string;
  hint?: string;
  value: string;
  error: string | null;
  onChange: (value: string) => void;
}) {
  return (
    <Field id={id} label={label} hint={hint} error={error}>
      <Textarea
        id={id}
        rows={6}
        className="font-mono"
        value={value}
        aria-invalid={!!error}
        aria-describedby={describedBy(id)}
        onChange={(event) => {
          onChange(event.target.value);
        }}
      />
    </Field>
  );
}

function FieldError({ id, children }: { id: string; children: ReactNode }) {
  return children ? (
    <p id={describedBy(id)} role="alert" className="text-sm text-danger">
      {children}
    </p>
  ) : null;
}
