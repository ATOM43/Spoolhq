import { X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { OpenSettingsLink, useAgentBlocker } from "@/features/settings";
import {
  cancelDraft,
  NewTicketForm,
  type TicketDraft,
} from "@/features/ticket-edit";
import { useProject } from "@/entities/project";
import { useTickets } from "@/entities/ticket";
import { Button, ConfirmDialog } from "@/shared/ui";

/**
 * The drawer on a ticket that doesn't exist yet: the edit form, empty (with Describe it
 * to draft it with the planner) or filled with `draft`. Nothing is saved until **Save**
 * (or **Save all**); the daemon assigns the ids, and `onSaved` then opens the (first)
 * ticket's own drawer.
 */
export function NewTicketDrawer({
  project,
  draft,
  onSaved,
  onClose,
}: {
  project: string;
  draft?: TicketDraft | undefined;
  onSaved: (id: string) => void;
  onClose: () => void;
}) {
  const tickets = useTickets(project);
  const [dirty, setDirty] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [stopping, setStopping] = useState(false);
  const agent = useAgentBlocker();
  const idle = useProject(project).data?.idle;
  // The daemon's own refusals, known before asking.
  const blocker = agent ?? (idle?.code === "no_commands" ? idle.message : null);
  const close = useCallback(() => {
    if (jobId !== null) {
      setStopping(true);
    } else if (dirty) {
      setLeaving(true);
    } else {
      onClose();
    }
  }, [dirty, jobId, onClose]);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      // A dialog open on top (a confirm) takes Escape for itself.
      if (event.key === "Escape" && !document.querySelector("dialog[open]")) {
        close();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
    };
  }, [close]);

  return (
    <aside
      aria-label="New ticket"
      className="absolute inset-y-0 right-0 z-40 flex w-[520px] max-w-full flex-col border-l bg-surface shadow-lg"
    >
      <header className="flex items-start gap-2 border-b p-4">
        <span className="rounded-sm bg-surface-sunken px-1.5 py-0.5 text-xs text-ink-muted">
          Assigned on save
        </span>
        <h2 className="min-w-0 flex-1 font-semibold">New ticket</h2>
        <Button variant="ghost" size="icon" aria-label="Close" onClick={close}>
          <X aria-hidden />
        </Button>
      </header>
      <div className="flex min-h-0 flex-1 flex-col gap-6 overflow-auto p-4">
        <NewTicketForm
          project={project}
          draft={draft}
          others={tickets.data?.tickets ?? []}
          blocker={blocker}
          blockerAction={<OpenSettingsLink reason={blocker} />}
          onSaved={onSaved}
          onClose={onClose}
          onDirtyChange={setDirty}
          onDraftingChange={setJobId}
        />
      </div>
      <ConfirmDialog
        open={leaving}
        title="Discard the new ticket?"
        consequence="The new ticket isn't saved and will be lost."
        action="Discard changes"
        destructive
        onCancel={() => {
          setLeaving(false);
        }}
        onConfirm={() => {
          setLeaving(false);
          onClose();
        }}
      />
      <ConfirmDialog
        open={stopping}
        title="Stop drafting?"
        consequence="The planner is still drafting; closing stops it and nothing is saved."
        action="Stop drafting"
        destructive
        onCancel={() => {
          setStopping(false);
        }}
        onConfirm={() => {
          setStopping(false);
          if (jobId !== null) {
            // The drawer goes now; the daemon stops the agent on its own time.
            void cancelDraft(project, jobId).catch(() => undefined);
          }
          onClose();
        }}
      />
    </aside>
  );
}
