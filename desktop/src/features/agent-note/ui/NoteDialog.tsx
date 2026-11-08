import { Play } from "lucide-react";
import { useId, useState, type ReactNode } from "react";

import { useRunLimits } from "@/entities/run";
import { useTicketDetail } from "@/entities/ticket";
import {
  Button,
  describedBy,
  Dialog,
  Field,
  ReasonButton,
  Textarea,
} from "@/shared/ui";

import { nextAttemptLine } from "../model/counter";
import { NOTE_MAX, useSendNote, type NoteKind } from "../model/send";

/**
 * D3 · Note to agent (480 px), shared by Unblock and Request changes: a required note
 * that the new attempt's prompt gets; for Unblock, a "Reset retry count" toggle.
 */
export function NoteDialog({
  project,
  ticketId,
  kind,
  open,
  summary,
  onClose,
  onStarted,
}: {
  project: string;
  ticketId: string;
  kind: NoteKind;
  open: boolean;
  /** The last failure or the review result, in a line or two. */
  summary: ReactNode;
  onClose: () => void;
  /** The attempt started: the caller switches to the Run tab. */
  onStarted: () => void;
}) {
  const id = useId();
  const [note, setNote] = useState("");
  const [reset, setReset] = useState(true);
  const send = useSendNote(project, ticketId);
  const counter = nextAttemptLine(
    useTicketDetail(project, ticketId).data?.ticket,
    useRunLimits(project),
    kind === "unblock" && reset,
  );
  const close = () => {
    send.reset();
    onClose();
  };
  const reason =
    note.trim() === ""
      ? "Write a note for the agent first"
      : send.isPending
        ? "Waiting for the daemon to answer"
        : null;

  return (
    <Dialog
      open={open}
      onClose={close}
      title={
        kind === "unblock"
          ? `Unblock ${ticketId}`
          : `Request changes on ${ticketId}`
      }
      className="max-w-[480px]"
    >
      <form
        className="flex flex-col gap-4"
        onSubmit={(event) => {
          event.preventDefault();
          if (reason === null) {
            send.mutate(
              { kind, note: note.trim(), resetRetries: reset },
              {
                onSuccess: () => {
                  setNote("");
                  close();
                  onStarted();
                },
              },
            );
          }
        }}
      >
        <div className="rounded-md border bg-surface-sunken p-3 text-sm">
          {summary}
        </div>
        <Field
          id={id}
          label="Note to the agent"
          hint={`Added to the next attempt's prompt. Up to ${String(NOTE_MAX)} characters.`}
        >
          <Textarea
            id={id}
            required
            maxLength={NOTE_MAX}
            rows={4}
            value={note}
            aria-describedby={describedBy(id)}
            onChange={(event) => {
              setNote(event.target.value);
            }}
          />
        </Field>
        {kind === "unblock" ? (
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={reset}
              onChange={(event) => {
                setReset(event.target.checked);
              }}
            />
            Reset retry count
          </label>
        ) : null}
        {send.isError ? (
          <p role="alert" className="text-sm text-danger">
            Couldn't start the attempt: {send.error.message}
          </p>
        ) : null}
        <div className="flex items-center justify-end gap-2 border-t pt-4">
          {counter ? (
            <p className="mr-auto text-xs text-ink-muted">{counter}</p>
          ) : null}
          <Button type="button" variant="outline" onClick={close}>
            Cancel
          </Button>
          <ReasonButton type="submit" reason={reason}>
            <Play aria-hidden />
            Start new attempt
          </ReasonButton>
        </div>
      </form>
    </Dialog>
  );
}
