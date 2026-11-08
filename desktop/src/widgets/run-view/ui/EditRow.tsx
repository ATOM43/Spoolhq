import {
  ChevronDown,
  ChevronRight,
  FilePen,
  SquareArrowOutUpRight,
} from "lucide-react";
import { useMemo } from "react";

import type { DiffReport } from "@/entities/run";
import { parsePatch } from "@/shared/lib";
import { Button } from "@/shared/ui";

import type { Row } from "../model/transcript";
import { DiffLines } from "./DiffLines";

/** Lines a mini diff shows before "Open in Diff". */
export const MINI_LINES = 50;

/**
 * A file edit; open, its lines from the attempt's diff for that path (the events carry
 * only the counts), cut at 50 with **Open in Diff**.
 */
export function EditRow({
  row,
  open,
  onToggle,
  diff,
  onOpenDiff,
}: {
  row: Extract<Row, { kind: "edit" }>;
  open: boolean;
  onToggle: () => void;
  diff: DiffReport | null | undefined;
  onOpenDiff: (path: string) => void;
}) {
  return (
    <div className="rounded-md border">
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
        <FilePen aria-hidden className="size-4 shrink-0 text-ink-muted" />
        <span className="text-ink-muted">Edited</span>
        <code className="min-w-0 flex-1 truncate font-mono text-xs">
          {row.path}
        </code>
        {row.added !== null ? (
          <span className="font-mono text-xs text-success">+{row.added}</span>
        ) : null}
        {row.removed !== null ? (
          <span className="font-mono text-xs text-danger">−{row.removed}</span>
        ) : null}
      </button>
      {open ? (
        <div className="border-t bg-surface-sunken px-3 py-2">
          <MiniDiff path={row.path} diff={diff} onOpenDiff={onOpenDiff} />
        </div>
      ) : null}
    </div>
  );
}

function MiniDiff({
  path,
  diff,
  onOpenDiff,
}: {
  path: string;
  diff: DiffReport | null | undefined;
  onOpenDiff: (path: string) => void;
}) {
  const file = diff?.files.find((f) => f.path === path);
  const lines = useMemo(() => parsePatch(file?.patch ?? ""), [file?.patch]);
  if (!diff) {
    return (
      <p className="text-xs text-ink-muted">
        The lines appear once the attempt's changes are committed.
      </p>
    );
  }
  if (!file) {
    return (
      <p className="text-xs text-ink-muted">
        This file isn't in the attempt's diff (changed back, or ignored).
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      {file.binary ? (
        <p className="text-xs text-ink-muted">Binary file, not shown.</p>
      ) : (
        <div className="max-h-96 overflow-auto rounded-sm border bg-surface">
          <DiffLines lines={lines.slice(0, MINI_LINES)} />
        </div>
      )}
      <div className="flex items-center gap-3">
        {lines.length > MINI_LINES ? (
          <span className="text-xs text-ink-muted">
            Showing {MINI_LINES} of {lines.length} lines
          </span>
        ) : null}
        <Button
          variant="link"
          size="sm"
          className="px-0"
          onClick={() => {
            onOpenDiff(path);
          }}
        >
          <SquareArrowOutUpRight aria-hidden />
          Open in Diff
        </Button>
      </div>
    </div>
  );
}
