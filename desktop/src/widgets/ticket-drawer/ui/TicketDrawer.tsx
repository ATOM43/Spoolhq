import { LoaderCircle, Pencil, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { TicketEditForm } from "@/features/ticket-edit";
import { useProject } from "@/entities/project";
import {
  TicketStatusBadge,
  useTicketDetail,
  useTickets,
  type Ticket,
  type TicketStatus,
} from "@/entities/ticket";
import { Button, ConfirmDialog, ReasonButton } from "@/shared/ui";

import { PrimaryAction } from "./PrimaryAction";
import { ReadSections } from "./ReadSections";
import {
  AttemptsSection,
  DetailState,
  GitSection,
  NeedsYouSection,
} from "./RunSections";
import { Section } from "./Section";

const LOCKED: Partial<Record<TicketStatus, string>> = {
  running: "Locked while the ticket is running",
  awaiting_approval: "Locked while the ticket is waiting for approval",
  done: "Done tickets can't be edited",
};

/**
 * The ticket drawer (screens spec section 7): 520 px from the right, over the tab
 * content. Esc or ✕ closes it; the page keeps `?ticket=` in the URL. The header has
 * the one primary action for the status; **Edit** turns the column into a form.
 */
export function TicketDrawer(props: {
  project: string;
  ticketId: string;
  onOpen: (id: string) => void;
  onClose: () => void;
  /** Switch to the Run tab, at an attempt when given. */
  onShowRun: (attempt?: number) => void;
}) {
  // Keyed, so opening another ticket leaves edit mode.
  return <Drawer key={props.ticketId} {...props} />;
}

function Drawer({
  project,
  ticketId,
  onOpen,
  onClose,
  onShowRun,
}: {
  project: string;
  ticketId: string;
  onOpen: (id: string) => void;
  onClose: () => void;
  onShowRun: (attempt?: number) => void;
}) {
  const tickets = useTickets(project);
  const detail = useTicketDetail(project, ticketId);
  const remote = useProject(project).data?.remote ?? null;
  const branch = useProject(project).data?.default_branch ?? "main";
  const [editing, setEditing] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const close = useCallback(() => {
    if (editing && dirty) {
      setLeaving(true);
    } else {
      onClose();
    }
  }, [editing, dirty, onClose]);

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

  const all = tickets.data?.tickets ?? [];
  const ticket = all.find((t) => t.id === ticketId);
  const status = ticket?.meta.status;
  const lock =
    (status && LOCKED[status]) ??
    (detail.isPending
      ? "Loading the ticket…"
      : detail.isError
        ? "Couldn't load the ticket"
        : null);

  return (
    <aside
      aria-label={`Ticket ${ticketId}`}
      className="absolute inset-y-0 right-0 z-40 flex w-[520px] max-w-full flex-col border-l bg-surface shadow-lg"
    >
      <header className="flex flex-col gap-3 border-b p-4">
        <div className="flex items-start gap-2">
          <span className="rounded-sm bg-surface-sunken px-1.5 py-0.5 font-mono text-xs">
            {ticketId}
          </span>
          <h2 className="min-w-0 flex-1 font-semibold">
            {ticket?.meta.title ?? ""}
          </h2>
          {ticket && !editing ? (
            <ReasonButton
              variant="ghost"
              size="sm"
              reason={lock}
              onClick={() => {
                setEditing(true);
              }}
            >
              <Pencil aria-hidden />
              Edit
            </ReasonButton>
          ) : null}
          <Button
            variant="ghost"
            size="icon"
            aria-label="Close"
            onClick={close}
          >
            <X aria-hidden />
          </Button>
        </div>
        {ticket && status ? (
          <>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
              <TicketStatusBadge status={status} />
              <span className="text-ink-muted">
                {detail.data?.ticket.run?.pr_number != null
                  ? `GitHub mode · PR #${String(detail.data.ticket.run.pr_number)}`
                  : remote
                    ? "GitHub mode"
                    : "Local mode · no GitHub remote"}
              </span>
              {lock && LOCKED[status] ? (
                <span className="text-ink-muted">{lock}</span>
              ) : null}
            </div>
            {editing ? null : (
              <PrimaryAction
                project={project}
                ticket={ticket}
                detail={detail.data?.ticket}
                all={all}
                onOpen={onOpen}
                onShowRun={onShowRun}
              />
            )}
          </>
        ) : null}
      </header>
      <div className="flex min-h-0 flex-1 flex-col gap-6 overflow-auto p-4">
        {tickets.isPending ? (
          <p className="flex items-center gap-2 text-sm text-ink-muted">
            <LoaderCircle aria-hidden className="size-4 animate-spin" />
            Loading {ticketId}…
          </p>
        ) : tickets.isError ? (
          <p role="alert" className="text-sm text-danger">
            Couldn't load the ticket: {tickets.error.message}
          </p>
        ) : !ticket ? (
          <div className="flex flex-col items-start gap-3">
            <p>This ticket no longer exists.</p>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        ) : editing && detail.data ? (
          <TicketEditForm
            key={detail.data.etag}
            project={project}
            ticket={detail.data.ticket}
            etag={detail.data.etag}
            others={all.filter((t) => t.id !== ticketId)}
            onDone={() => {
              setEditing(false);
            }}
            onReload={() => void detail.refetch()}
            onDirtyChange={setDirty}
          />
        ) : (
          <Columns
            ticket={ticket}
            all={all}
            project={project}
            branch={branch}
            detail={detail}
            onOpen={onOpen}
            onShowRun={onShowRun}
          />
        )}
      </div>
      <ConfirmDialog
        open={leaving}
        title="Discard your changes?"
        consequence={`Your edits to ${ticketId} aren't saved and will be lost.`}
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
    </aside>
  );
}

function Columns({
  ticket,
  all,
  project,
  branch,
  detail,
  onOpen,
  onShowRun,
}: {
  ticket: Ticket;
  all: readonly Ticket[];
  project: string;
  branch: string;
  detail: ReturnType<typeof useTicketDetail>;
  onOpen: (id: string) => void;
  onShowRun: (attempt?: number) => void;
}) {
  const status = ticket.meta.status;
  const data = detail.data?.ticket;
  return (
    <>
      {status === "blocked" || status === "awaiting_approval" ? (
        <DetailState query={detail}>
          {data ? (
            <NeedsYouSection
              ticket={ticket}
              detail={data}
              onShowRun={onShowRun}
            />
          ) : null}
        </DetailState>
      ) : null}
      <ReadSections
        project={project}
        ticket={ticket}
        all={all}
        onOpen={onOpen}
      />
      <Section title="Attempts">
        <DetailState query={detail}>
          {data ? (
            <AttemptsSection attempts={data.attempts} onShowRun={onShowRun} />
          ) : null}
        </DetailState>
      </Section>
      <Section title="Git">
        <DetailState query={detail}>
          {data ? <GitSection git={data.git} branch={branch} /> : null}
        </DetailState>
      </Section>
    </>
  );
}
