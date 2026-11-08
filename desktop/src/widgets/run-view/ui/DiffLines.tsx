import type { DiffLine } from "@/shared/lib";
import { cn } from "@/shared/lib";

const TONE: Record<DiffLine["kind"], string> = {
  hunk: "bg-surface-sunken text-ink-muted",
  add: "bg-success/10 text-success",
  del: "bg-danger/10 text-danger",
  context: "",
  note: "text-ink-muted italic",
};
const SIGN: Record<DiffLine["kind"], string> = {
  hunk: "",
  add: "+",
  del: "−",
  context: " ",
  note: "",
};

/** Unified diff lines with both line numbers; plain text only (untrusted). */
export function DiffLines({ lines }: { lines: readonly DiffLine[] }) {
  return (
    <pre className="overflow-auto font-mono text-xs leading-5">
      {/* Lines are positional and never reorder, so the index is their key. */}
      {lines.map((line, index) => (
        <div
          key={index}
          data-kind={line.kind}
          className={cn("flex min-w-max", TONE[line.kind])}
        >
          <span className="w-10 shrink-0 pr-2 text-right text-ink-muted select-none">
            {line.old ?? ""}
          </span>
          <span className="w-10 shrink-0 pr-2 text-right text-ink-muted select-none">
            {line.new ?? ""}
          </span>
          <span className="w-4 shrink-0 select-none">{SIGN[line.kind]}</span>
          <span className="pr-3">{line.text}</span>
        </div>
      ))}
    </pre>
  );
}
