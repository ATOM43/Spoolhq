import { CircleAlert, CircleCheck, CircleX, Clock } from "lucide-react";

import { cn } from "@/shared/lib";

import type { CommandTestResult } from "../model/api";

function describe(result: CommandTestResult) {
  switch (result.status) {
    case "passed":
      return {
        icon: <CircleCheck aria-hidden />,
        label: "Passed",
        tone: "text-success",
      };
    case "failed":
      return {
        icon: <CircleX aria-hidden />,
        label: `Failed (exit ${String(result.exit_code)})`,
        tone: "text-danger",
      };
    case "timed_out":
      return {
        icon: <Clock aria-hidden />,
        label: `Timed out after ${String(result.timeout_s)} s`,
        tone: "text-danger",
      };
    case "error":
      return {
        icon: <CircleAlert aria-hidden />,
        label: "Couldn't run",
        tone: "text-danger",
      };
  }
}

/** A Test run's outcome as icon + label, and its trimmed output. */
export function CommandResult({ result }: { result: CommandTestResult }) {
  const { icon, label, tone } = describe(result);
  return (
    <div className="flex flex-col gap-1.5" role="status">
      <span
        className={cn(
          "inline-flex items-center gap-1.5 text-sm [&_svg]:size-4",
          tone,
        )}
      >
        {icon}
        <span className="text-ink">
          {label} · {result.duration_s.toFixed(1)} s
        </span>
      </span>
      {result.output ? (
        <pre className="max-h-40 overflow-auto rounded-md border bg-surface-sunken p-2 font-mono text-xs whitespace-pre-wrap">
          {result.output}
          {result.output_truncated ? "\n[output cut]" : ""}
        </pre>
      ) : null}
    </div>
  );
}
