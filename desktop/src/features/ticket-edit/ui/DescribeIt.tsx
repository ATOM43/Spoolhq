import { LoaderCircle, TriangleAlert } from "lucide-react";
import { useId, type ReactNode } from "react";

import {
  Button,
  describedBy,
  Field,
  ReasonButton,
  Textarea,
} from "@/shared/ui";

import { REQUEST_MAX } from "../model/drafting";

/**
 * The top of the empty Add ticket form: a few lines for the planner, **Draft with
 * planner**, and while it drafts a spinner with Cancel. A failed or refused draft shows
 * its message with Try again, which sends the same text.
 */
export function DescribeIt({
  request,
  onRequestChange,
  blocker,
  blockerAction,
  starting,
  drafting,
  cancelling,
  failure,
  onDraft,
  onCancel,
}: {
  request: string;
  onRequestChange: (request: string) => void;
  /** Why the daemon would refuse to draft, or null. */
  blocker: string | null;
  /** What to do about `blocker` (Open Settings), shown next to the button. */
  blockerAction?: ReactNode;
  starting: boolean;
  drafting: boolean;
  cancelling: boolean;
  failure: string | null;
  onDraft: () => void;
  onCancel: () => void;
}) {
  const id = useId();
  const reason =
    blocker ??
    (drafting
      ? "The planner is drafting already"
      : starting
        ? "Waiting for the daemon to answer"
        : request.trim() === ""
          ? "Describe the ticket first"
          : null);
  return (
    <section
      aria-label="Draft with the planner"
      className="flex flex-col gap-2 rounded-md border bg-surface-sunken p-3"
    >
      <Field
        id={id}
        label="Describe it"
        hint="A few lines; the planner drafts one to three tickets for you to check."
      >
        <Textarea
          id={id}
          rows={3}
          maxLength={REQUEST_MAX}
          value={request}
          disabled={drafting}
          aria-describedby={`${describedBy(id)} ${id}-count`}
          onChange={(event) => {
            onRequestChange(event.target.value);
          }}
        />
      </Field>
      <div className="flex flex-wrap items-center gap-2">
        <ReasonButton type="button" reason={reason} onClick={onDraft}>
          Draft with planner
        </ReasonButton>
        {blockerAction}
        {drafting ? (
          <>
            <span role="status" className="flex items-center gap-1.5 text-sm">
              <LoaderCircle aria-hidden className="size-4 animate-spin" />
              Drafting…
            </span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={cancelling}
              onClick={onCancel}
            >
              Cancel
            </Button>
          </>
        ) : null}
        <span id={`${id}-count`} className="ml-auto text-xs text-ink-muted">
          {request.length.toLocaleString("en")} /{" "}
          {REQUEST_MAX.toLocaleString("en")}
        </span>
      </div>
      {failure ? (
        <div role="alert" className="flex flex-wrap items-center gap-2 text-sm">
          <TriangleAlert aria-hidden className="size-4 text-danger" />
          <span>{failure}</span>
          {blocker === null && request.trim() !== "" ? (
            <Button
              type="button"
              variant="link"
              size="sm"
              className="px-0"
              onClick={onDraft}
            >
              Try again
            </Button>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
