import {
  CirclePause,
  CircleSlash,
  LoaderCircle,
  Play,
  Square,
  StepForward,
} from "lucide-react";
import { useState } from "react";

import { ConfirmDialog, ReasonButton } from "@/shared/ui";

import { useRunAction, type RunAction } from "../model/run";
import type { PanelState } from "../model/state";

/** V2 header, row 2 right: the run controls for the project's state. */
export function RunControls({
  project,
  state,
  usage,
  offline,
}: {
  project: string;
  state: PanelState;
  usage: string | null;
  /** Why every control is disabled (the daemon is gone), or null. */
  offline: string | null;
}) {
  const action = useRunAction(project);
  const [confirmCancel, setConfirmCancel] = useState(false);
  const busy = action.isPending ? "Waiting for the daemon to answer" : null;
  const reason = offline ?? busy;
  const startReason = offline ?? (state.kind === "idle" ? state.reason : busy);
  const run = (what: RunAction) => {
    action.mutate(what);
  };
  const cancel = (
    <>
      <ReasonButton
        variant="outline"
        reason={reason}
        onClick={() => {
          setConfirmCancel(true);
        }}
      >
        <Square aria-hidden />
        Cancel
      </ReasonButton>
      <ConfirmDialog
        open={confirmCancel}
        title={`Cancel ${"ticket" in state ? state.ticket : "the run"}?`}
        consequence={`The worktree is removed and the ticket returns to Ready.${usage ? ` Used so far: ${usage}.` : ""}`}
        action="Cancel run"
        destructive
        onCancel={() => {
          setConfirmCancel(false);
        }}
        onConfirm={() => {
          setConfirmCancel(false);
          run("cancel");
        }}
      />
    </>
  );

  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      {state.kind === "running" ? (
        <>
          <span className="flex items-center gap-1.5 text-sm text-accent">
            <LoaderCircle aria-hidden className="size-4 animate-spin" />
            Running {state.ticket}
            {state.step ? ` · ${state.step}` : ""}
            {state.attempt > 1 ? ` · attempt ${String(state.attempt)}` : ""}
          </span>
          <ReasonButton
            variant="outline"
            reason={reason}
            onClick={() => {
              run("pause");
            }}
          >
            <CirclePause aria-hidden />
            Pause
          </ReasonButton>
          {cancel}
        </>
      ) : state.kind === "paused" ? (
        <>
          <span className="flex items-center gap-1.5 text-sm text-warning">
            <CirclePause aria-hidden className="size-4" />
            Paused {state.ticket}
          </span>
          <ReasonButton
            reason={reason}
            onClick={() => {
              run("resume");
            }}
          >
            <Play aria-hidden />
            Resume
          </ReasonButton>
          {cancel}
        </>
      ) : state.kind === "paused_limit" ? (
        <>
          <span className="flex items-center gap-1.5 text-sm text-warning">
            <CirclePause aria-hidden className="size-4" />
            Paused · usage limit
            {state.resumesAt ? ` · resumes ${state.resumesAt}` : ""}
          </span>
          {cancel}
        </>
      ) : (
        <>
          {state.kind === "idle" ? (
            <span className="flex items-center gap-1.5 text-sm text-ink-muted">
              <CircleSlash aria-hidden className="size-4" />
              Idle
            </span>
          ) : null}
          <ReasonButton
            reason={startReason}
            onClick={() => {
              run("next");
            }}
          >
            <StepForward aria-hidden />
            Run next{state.kind === "ready" ? ` (${state.next})` : ""}
          </ReasonButton>
          <ReasonButton
            variant="outline"
            reason={startReason}
            onClick={() => {
              run("all");
            }}
          >
            <Play aria-hidden />
            Run all
          </ReasonButton>
        </>
      )}
      {action.error ? (
        <p role="alert" className="w-full text-right text-sm text-danger">
          {action.error.message}
        </p>
      ) : null}
    </div>
  );
}
