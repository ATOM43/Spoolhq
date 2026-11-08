import {
  ChevronDown,
  ChevronRight,
  CircleCheck,
  CircleMinus,
  CircleX,
  LoaderCircle,
  TimerOff,
  type LucideIcon,
} from "lucide-react";
import { useLayoutEffect, useRef, useState } from "react";

import type { GateReport, GatesReport } from "@/entities/run";
import { cn } from "@/shared/lib";

import { formatDuration, type LiveDetails } from "../model/details";
import { Note } from "./Note";

type RowState = GateReport["state"] | "running";

const LOOK: Record<
  RowState,
  { icon: LucideIcon; tone: string; label: string }
> = {
  passed: { icon: CircleCheck, tone: "text-success", label: "Passed" },
  failed: { icon: CircleX, tone: "text-danger", label: "Failed" },
  timed_out: { icon: TimerOff, tone: "text-danger", label: "Timed out" },
  skipped: { icon: CircleMinus, tone: "text-ink-muted", label: "Skipped" },
  running: { icon: LoaderCircle, tone: "text-accent", label: "Running" },
};

const failing = (state: RowState) =>
  state === "failed" || state === "timed_out";

/** The progress event's status (`error` is a failure, as in the report). */
const asState = (status: string): RowState =>
  status in LOOK && status !== "running"
    ? (status as RowState)
    : status === "error"
      ? "failed"
      : "skipped";

/**
 * One row per gate command. A failed row opens on its own and scrolls to the first
 * failure line; output is plain monospace text (untrusted). While the gates run, the
 * rows done so far come from the step events, then "Running <command>…".
 */
export function GatesPanel({
  report,
  live,
  ended,
}: {
  report: GatesReport | null;
  live: LiveDetails;
  ended: boolean;
}) {
  // Rows the user opened or closed, against each row's default (failed: open).
  const [toggled, setToggled] = useState<ReadonlySet<string>>(new Set());
  if (report === null) {
    if (live.gates === null) {
      return (
        <Note>
          {ended
            ? "No gates ran in this attempt."
            : "Gates run after the agent finishes."}
        </Note>
      );
    }
    return (
      <ul aria-label="Gates" className="flex flex-col rounded-md border">
        {live.gates.done.map((gate) => (
          <li key={gate.name} className="border-b">
            <RowHead
              name={gate.name}
              command={gate.command}
              state={asState(gate.status)}
              ms={gate.duration_ms}
            />
          </li>
        ))}
        <li className="flex items-center gap-2 px-3 py-2 text-sm text-accent">
          <LoaderCircle
            aria-hidden
            className="size-4 motion-safe:animate-spin"
          />
          Running{" "}
          <code className="font-mono text-xs">{live.gates.command ?? "…"}</code>
          …
        </li>
      </ul>
    );
  }
  if (report.stopped) {
    return (
      <Note>
        The agent stopped early ({report.stopped.replace("_", " ")}), so no gate
        ran.
      </Note>
    );
  }
  return (
    <ul aria-label="Gates" className="flex flex-col divide-y rounded-md border">
      {report.results.map((gate) => {
        const open = failing(gate.state) !== toggled.has(gate.name);
        const canOpen = gate.output !== "";
        return (
          <li key={gate.name}>
            <RowHead
              name={gate.name}
              command={gate.command}
              state={gate.state}
              ms={gate.state === "skipped" ? null : gate.duration_ms}
              open={canOpen ? open : undefined}
              onToggle={() => {
                setToggled((previous) => {
                  const next = new Set(previous);
                  if (!next.delete(gate.name)) {
                    next.add(gate.name);
                  }
                  return next;
                });
              }}
            />
            {canOpen && open ? <Output gate={gate} /> : null}
          </li>
        );
      })}
    </ul>
  );
}

function RowHead({
  name,
  command,
  state,
  ms,
  open,
  onToggle,
}: {
  name: string;
  command: string;
  state: RowState;
  ms: number | null;
  /** undefined: nothing to expand. */
  open?: boolean | undefined;
  onToggle?: () => void;
}) {
  const { icon: Icon, tone, label } = LOOK[state];
  const content = (
    <>
      {open === undefined ? (
        <span className="size-4 shrink-0" />
      ) : open ? (
        <ChevronDown aria-hidden className="size-4 shrink-0" />
      ) : (
        <ChevronRight aria-hidden className="size-4 shrink-0" />
      )}
      <span className="w-12 shrink-0 text-xs text-ink-muted">{name}</span>
      <code className="min-w-0 flex-1 truncate font-mono text-xs">
        {command || "not set"}
      </code>
      <span className={cn("flex items-center gap-1 text-xs", tone)}>
        <Icon aria-hidden className="size-4" />
        {label}
      </span>
      <span className="w-14 text-right font-mono text-xs text-ink-muted">
        {ms === null ? "—" : formatDuration(ms)}
      </span>
    </>
  );
  const className =
    "flex w-full items-center gap-2 px-3 py-2 text-left text-sm";
  return open === undefined ? (
    <div className={className}>{content}</div>
  ) : (
    <button
      type="button"
      aria-expanded={open}
      onClick={onToggle}
      className={cn(
        className,
        "outline-none hover:bg-surface-sunken focus-visible:ring-[3px] focus-visible:ring-accent/50",
      )}
    >
      {content}
    </button>
  );
}

function Output({ gate }: { gate: GateReport }) {
  const box = useRef<HTMLPreElement>(null);
  const mark = useRef<HTMLSpanElement>(null);
  useLayoutEffect(() => {
    // Within the output box only, so the page itself doesn't jump.
    if (box.current && mark.current) {
      box.current.scrollTop =
        mark.current.offsetTop - box.current.clientHeight / 2;
    }
  }, []);
  const lines = gate.output.split("\n");
  return (
    <div className="border-t bg-surface-sunken px-3 py-2">
      <pre
        ref={box}
        className="relative max-h-80 overflow-auto font-mono text-xs whitespace-pre-wrap"
      >
        {/* Lines are positional and never reorder, so the index is their key. */}
        {lines.map((line, index) =>
          index === gate.first_failure_line ? (
            <span
              key={index}
              ref={mark}
              data-failure
              className="block bg-danger/15 font-semibold text-danger"
            >
              <span className="sr-only">First failure: </span>
              {line}
            </span>
          ) : (
            <span key={index} className="block">
              {line}
            </span>
          ),
        )}
      </pre>
      {gate.truncated ? (
        <p className="mt-2 text-xs text-ink-muted">
          Output trimmed: the full log is in the attempt folder.
        </p>
      ) : null}
    </div>
  );
}
