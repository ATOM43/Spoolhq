import { Check, Copy } from "lucide-react";
import { Button } from "./button";
import { useCopy } from "./use-copy";

/** A small icon button that copies `text` (a path, a branch). */
export function CopyButton({ text, label }: { text: string; label: string }) {
  const { state, copy } = useCopy(text);
  return (
    <Button
      variant="ghost"
      size="icon-sm"
      aria-label={state === "failed" ? `${label} (select and copy)` : label}
      title={state === "copied" ? "Copied" : label}
      onClick={() => void copy()}
    >
      {state === "copied" ? <Check aria-hidden /> : <Copy aria-hidden />}
    </Button>
  );
}

/** A shell command shown in monospace with a Copy button. */
export function CopyCommand({ command }: { command: string }) {
  const { state, copy } = useCopy(command);

  return (
    <div className="flex items-center justify-between gap-4 rounded-md border bg-surface-sunken py-1 pr-1 pl-4">
      {/* select-all: one click selects the command if the clipboard is unavailable. */}
      <code className="font-mono text-sm select-all">{command}</code>
      <Button
        variant="ghost"
        size="sm"
        aria-label={`Copy ${command}`}
        onClick={() => void copy()}
      >
        {state === "copied" ? <Check aria-hidden /> : <Copy aria-hidden />}
        {state === "copied"
          ? "Copied"
          : state === "failed"
            ? "Select and copy"
            : "Copy"}
      </Button>
    </div>
  );
}
