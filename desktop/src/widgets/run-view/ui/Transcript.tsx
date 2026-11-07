import {
  ArrowDown,
  ChevronDown,
  ChevronRight,
  FilePen,
  FileText,
  Info,
  LoaderCircle,
  ShieldX,
  SquareTerminal,
} from "lucide-react";
import { useLayoutEffect, useRef, useState } from "react";

import { cn } from "@/shared/lib";
import { Button, Markdown } from "@/shared/ui";

import type { Row } from "../model/transcript";

/** Rows rendered at once; **Show earlier** adds this many. No virtualising library. */
export const PAGE_ROWS = 500;
const RESULT_LINES = 200;
// Within this many pixels of the end counts as "at the bottom".
const NEAR_END_PX = 40;

/**
 * The live transcript. Everything in it is untrusted: agent messages go through the
 * safe `Markdown` (no HTML, links inert), tool output is plain monospace text.
 * Follows new rows while scrolled to the end; scrolled up, a "Jump to latest" pill.
 */
export function Transcript({ rows }: { rows: readonly Row[] }) {
  const scroller = useRef<HTMLDivElement>(null);
  const [atEnd, setAtEnd] = useState(true);
  const [shown, setShown] = useState(PAGE_ROWS);
  const [open, setOpen] = useState<ReadonlySet<number>>(new Set());
  const visible = rows.slice(-shown);
  const count = rows.length;

  const toEnd = () => {
    const element = scroller.current;
    if (element) {
      element.scrollTop = element.scrollHeight;
    }
  };
  useLayoutEffect(() => {
    if (atEnd) {
      toEnd();
    }
  }, [count, atEnd]);

  if (count === 0) {
    return (
      <p className="flex items-center gap-2 p-6 text-sm text-ink-muted">
        <LoaderCircle aria-hidden className="size-4 motion-safe:animate-spin" />
        Waiting for the agent…
      </p>
    );
  }
  return (
    <div className="relative flex min-h-0 flex-1 flex-col">
      <div
        ref={scroller}
        aria-label="Transcript"
        role="log"
        tabIndex={0}
        onScroll={(event) => {
          const element = event.currentTarget;
          const gap =
            element.scrollHeight - element.scrollTop - element.clientHeight;
          setAtEnd(gap <= NEAR_END_PX);
        }}
        className="flex min-h-0 flex-1 flex-col gap-3 overflow-auto p-6 outline-none"
      >
        {count > shown ? (
          <Button
            variant="outline"
            size="sm"
            className="self-center"
            onClick={() => {
              setShown((n) => n + PAGE_ROWS);
            }}
          >
            Show earlier ({String(count - shown)} more)
          </Button>
        ) : null}
        {visible.map((row) => (
          <RowView
            key={row.seq}
            row={row}
            open={open.has(row.seq)}
            onToggle={() => {
              setOpen((previous) => {
                const next = new Set(previous);
                if (!next.delete(row.seq)) {
                  next.add(row.seq);
                }
                return next;
              });
            }}
          />
        ))}
      </div>
      {atEnd ? null : (
        <Button
          variant="outline"
          size="sm"
          className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full shadow-md"
          onClick={() => {
            toEnd();
            setAtEnd(true);
          }}
        >
          <ArrowDown aria-hidden />
          Jump to latest
        </Button>
      )}
    </div>
  );
}

function RowView({
  row,
  open,
  onToggle,
}: {
  row: Row;
  open: boolean;
  onToggle: () => void;
}) {
  switch (row.kind) {
    case "message":
      return (
        <div className="flex flex-col gap-1">
          <p className="text-xs text-ink-muted">Agent</p>
          <Markdown source={row.text} />
        </div>
      );
    case "tool":
      return <ToolRow row={row} open={open} onToggle={onToggle} />;
    case "denied":
      return (
        <div className="flex items-center gap-2 rounded-md border border-danger/50 bg-danger/10 px-3 py-2 text-sm text-danger">
          <ShieldX aria-hidden className="size-4 shrink-0" />
          <span className="font-medium">Denied by policy</span>
          <code className="truncate font-mono text-xs">
            {row.tool} {row.command}
          </code>
        </div>
      );
    case "edit":
      return (
        <div className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm">
          <FilePen aria-hidden className="size-4 shrink-0 text-ink-muted" />
          <span className="text-ink-muted">Edited</span>
          <code className="min-w-0 flex-1 truncate font-mono text-xs">
            {row.path}
          </code>
          {row.added !== null ? (
            <span className="font-mono text-xs text-success">+{row.added}</span>
          ) : null}
          {row.removed !== null ? (
            <span className="font-mono text-xs text-danger">
              −{row.removed}
            </span>
          ) : null}
        </div>
      );
    case "note":
      return (
        <p className="flex items-center gap-2 text-xs text-ink-muted">
          <Info aria-hidden className="size-3.5 shrink-0" />
          {row.text}
        </p>
      );
  }
}

function ToolRow({
  row,
  open,
  onToggle,
}: {
  row: Extract<Row, { kind: "tool" }>;
  open: boolean;
  onToggle: () => void;
}) {
  const Icon = row.name === "Bash" ? SquareTerminal : FileText;
  const lines = row.result?.text.split("\n").slice(0, RESULT_LINES) ?? [];
  return (
    <div
      className={cn(
        "rounded-md border",
        row.result?.isError && "border-danger/50",
      )}
    >
      <button
        type="button"
        aria-expanded={open}
        onClick={onToggle}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm outline-none focus-visible:ring-[3px] focus-visible:ring-accent/50"
      >
        {open ? (
          <ChevronDown aria-hidden className="size-4 shrink-0" />
        ) : (
          <ChevronRight aria-hidden className="size-4 shrink-0" />
        )}
        <Icon aria-hidden className="size-4 shrink-0 text-ink-muted" />
        <span className="font-mono text-xs font-semibold">{row.name}</span>
        <code className="min-w-0 flex-1 truncate font-mono text-xs text-ink-muted">
          {row.target}
        </code>
        {row.seconds === null ? (
          <span className="flex items-center gap-1 text-xs text-accent">
            <LoaderCircle
              aria-hidden
              className="size-3.5 motion-safe:animate-spin"
            />
            Running
          </span>
        ) : (
          <span className="font-mono text-xs text-ink-muted">
            {row.result?.isError ? "Failed · " : ""}
            {row.seconds.toFixed(1)}s
          </span>
        )}
      </button>
      {open ? (
        <div className="border-t bg-surface-sunken px-3 py-2">
          {row.result === null ? (
            <p className="text-xs text-ink-muted">No result yet.</p>
          ) : (
            <>
              <pre className="max-h-96 overflow-auto font-mono text-xs whitespace-pre-wrap">
                {lines.join("\n")}
              </pre>
              {row.result.lines > RESULT_LINES ? (
                <p className="mt-2 text-xs text-ink-muted">
                  Showing {RESULT_LINES} of {row.result.lines} lines
                </p>
              ) : null}
            </>
          )}
        </div>
      ) : null}
    </div>
  );
}
