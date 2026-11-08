import {
  FileMinus,
  FilePen,
  FilePlus,
  FileSymlink,
  type LucideIcon,
} from "lucide-react";
import { useMemo } from "react";

import type { DiffFile, DiffReport } from "@/entities/run";
import { cn, parsePatch } from "@/shared/lib";

import { DiffLines } from "./DiffLines";
import { Note } from "./Note";

const STATUS: Record<
  DiffFile["status"],
  { icon: LucideIcon; tone: string; label: string }
> = {
  added: { icon: FilePlus, tone: "text-success", label: "Added" },
  modified: { icon: FilePen, tone: "text-ink-muted", label: "Modified" },
  deleted: { icon: FileMinus, tone: "text-danger", label: "Deleted" },
  renamed: { icon: FileSymlink, tone: "text-accent", label: "Renamed" },
};

export function Counts({
  file,
}: {
  file: Pick<DiffFile, "additions" | "deletions">;
}) {
  return (
    <span className="shrink-0 font-mono text-xs">
      <span className="text-success">+{file.additions}</span>{" "}
      <span className="text-danger">−{file.deletions}</span>
    </span>
  );
}

/** The changed files with totals, and the selected file's unified diff. */
export function DiffPanel({
  report,
  ended,
  selected,
  onSelect,
}: {
  report: DiffReport | null;
  ended: boolean;
  /** The selected path; the first file when null or gone. */
  selected: string | null;
  onSelect: (path: string) => void;
}) {
  if (report === null) {
    return (
      <Note>
        {ended
          ? "This attempt changed no files."
          : "The diff appears once the agent has changed files."}
      </Note>
    );
  }
  if (report.files.length === 0) {
    return <Note>This attempt changed no files.</Note>;
  }
  const file = report.files.find((f) => f.path === selected) ?? report.files[0];
  const additions = report.files.reduce((sum, f) => sum + f.additions, 0);
  const deletions = report.files.reduce((sum, f) => sum + f.deletions, 0);
  return (
    <div className="flex min-h-0 flex-col gap-3">
      <p className="flex items-center gap-2 text-sm">
        <span className="font-medium">
          {report.files.length} {report.files.length === 1 ? "file" : "files"}
        </span>
        <Counts file={{ additions, deletions }} />
      </p>
      <ul
        aria-label="Changed files"
        className="flex flex-col divide-y rounded-md border"
      >
        {report.files.map((f) => {
          const { icon: Icon, tone, label } = STATUS[f.status];
          return (
            <li key={f.path}>
              <button
                type="button"
                aria-pressed={f.path === file?.path}
                onClick={() => {
                  onSelect(f.path);
                }}
                className={cn(
                  "flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm outline-none hover:bg-surface-sunken focus-visible:ring-[3px] focus-visible:ring-accent/50",
                  f.path === file?.path && "bg-surface-sunken font-medium",
                )}
              >
                <span className={cn("flex items-center gap-1 text-xs", tone)}>
                  <Icon aria-hidden className="size-4" />
                  <span className="sr-only">{label}</span>
                </span>
                <code
                  className="min-w-0 flex-1 truncate font-mono text-xs"
                  title={f.path}
                >
                  {f.old_path ? `${f.old_path} → ${f.path}` : f.path}
                </code>
                {f.binary ? (
                  <span className="text-xs text-ink-muted">binary</span>
                ) : (
                  <Counts file={f} />
                )}
              </button>
            </li>
          );
        })}
      </ul>
      {file ? <FileDiff file={file} /> : null}
    </div>
  );
}

function FileDiff({ file }: { file: DiffFile }) {
  const lines = useMemo(() => parsePatch(file.patch), [file.patch]);
  const { label } = STATUS[file.status];
  return (
    <section
      aria-label={`Diff of ${file.path}`}
      className="flex flex-col rounded-md border"
    >
      <p className="border-b px-3 py-1.5 text-xs text-ink-muted">
        {label} · <code className="font-mono">{file.path}</code>
      </p>
      {file.binary ? (
        <p className="px-3 py-2 text-sm text-ink-muted">
          Binary file, not shown.
        </p>
      ) : lines.length === 0 ? (
        <p className="px-3 py-2 text-sm text-ink-muted">
          No line changes (the file mode or name changed).
        </p>
      ) : (
        <div className="max-h-[60vh] overflow-auto">
          <DiffLines lines={lines} />
        </div>
      )}
      {file.truncated ? (
        <p className="border-t px-3 py-1.5 text-xs text-ink-muted">
          Diff cut at 2,000 lines.
        </p>
      ) : null}
    </section>
  );
}
