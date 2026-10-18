import { Check, Copy } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

type CopyState = "idle" | "copied" | "failed";

/** A shell command shown in monospace with a Copy button. */
export function CopyCommand({ command }: { command: string }) {
  const [state, setState] = useState<CopyState>("idle");

  async function copy() {
    try {
      await navigator.clipboard.writeText(command);
      setState("copied");
    } catch {
      setState("failed");
    }
  }

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
