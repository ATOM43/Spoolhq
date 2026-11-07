import {
  CircleAlert,
  CircleCheck,
  CirclePause,
  CircleSlash,
  CircleX,
  Eye,
} from "lucide-react";
import type { ReactNode } from "react";

import type { RunDetail } from "@/entities/run";
import { Button } from "@/shared/ui";

const time = (iso: string) =>
  new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

const sentence = (text: string | null): string =>
  text ? text.charAt(0).toUpperCase() + text.slice(1) : "";

/**
 * The end of a run and its next action (screens spec, Run tab): merged (with the next
 * ticket when one started), blocked (Unblock), needs approval (Review), paused by a
 * usage limit (it resumes by itself), cancelled or interrupted (Run next).
 */
export function ResultPanel({
  run,
  commit,
  next,
  onViewNext,
  onOpenTicket,
  runNext,
}: {
  run: RunDetail;
  /** The squash commit's short sha, once merged. */
  commit: string | null;
  /** The ticket of the run that started after this one, if any. */
  next: string | null;
  onViewNext: () => void;
  onOpenTicket: (id: string) => void;
  runNext: ReactNode;
}) {
  const open = () => {
    onOpenTicket(run.ticket_id);
  };
  switch (run.status) {
    case "done":
      return (
        <Result icon={<CircleCheck />} tone="text-success">
          <span>{commit ? `Merged as ${commit}` : "Merged"}</span>
          {next ? (
            <>
              <span className="text-ink-muted">· Next: {next} started</span>
              <Button size="sm" variant="outline" onClick={onViewNext}>
                View {next}
              </Button>
            </>
          ) : null}
        </Result>
      );
    case "blocked":
      return (
        <Result icon={<CircleX />} tone="text-danger">
          <span>Blocked: {run.reason ?? "no reason recorded"}</span>
          <Button size="sm" onClick={open}>
            Unblock
          </Button>
        </Result>
      );
    case "awaiting_approval":
      return (
        <Result icon={<Eye />} tone="text-warning">
          <span>Needs approval: {run.reason ?? "a person decides"}</span>
          <Button size="sm" onClick={open}>
            Review
          </Button>
        </Result>
      );
    case "paused":
      return (
        <Result icon={<CirclePause />} tone="text-warning">
          <span>
            Paused · resumes {run.reset_at ? time(run.reset_at) : "later"}
          </span>
          <span className="text-ink-muted">The run continues by itself.</span>
        </Result>
      );
    case "cancelled":
      return (
        <Result icon={<CircleSlash />} tone="text-ink-muted">
          <span>Cancelled</span>
          {runNext}
        </Result>
      );
    default:
      return (
        <Result icon={<CircleAlert />} tone="text-warning">
          <span>
            Interrupted{run.reason ? `: ${sentence(run.reason)}` : ""}
          </span>
          {runNext}
        </Result>
      );
  }
}

function Result({
  icon,
  tone,
  children,
}: {
  icon: ReactNode;
  tone: string;
  children: ReactNode;
}) {
  return (
    <div
      role="status"
      className="flex flex-wrap items-center gap-2 text-sm font-medium"
    >
      <span className={`flex items-center [&_svg]:size-4 ${tone}`} aria-hidden>
        {icon}
      </span>
      {children}
    </div>
  );
}
