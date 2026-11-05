import {
  Circle,
  CircleCheck,
  CircleMinus,
  CircleX,
  LoaderCircle,
} from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/shared/lib";

import type { Job, JobStep } from "../model/api";
import { stepTitle, type Form } from "../model/form";

const LOOK: Record<
  JobStep["state"],
  { icon: ReactNode; label: string; tone: string }
> = {
  pending: {
    icon: <Circle aria-hidden />,
    label: "Pending",
    tone: "text-ink-muted",
  },
  running: {
    icon: <LoaderCircle aria-hidden className="animate-spin" />,
    label: "Running",
    tone: "text-accent",
  },
  passed: {
    icon: <CircleCheck aria-hidden />,
    label: "Passed",
    tone: "text-success",
  },
  failed: {
    icon: <CircleX aria-hidden />,
    label: "Failed",
    tone: "text-danger",
  },
  skipped: {
    icon: <CircleMinus aria-hidden />,
    label: "Skipped",
    tone: "text-ink-muted",
  },
};

function rollbackLine(job: Job): string | null {
  if (!job.rollback) {
    return null;
  }
  return job.rollback.left.length > 0
    ? `Left behind: ${job.rollback.left.join(", ")}`
    : "Rolled back";
}

/** "Creating the project": each step's state as icon + label; a failure expands. */
export function Checklist({ job, form }: { job: Job; form?: Form }) {
  const rollback = rollbackLine(job);
  return (
    <section
      aria-label="Creating the project"
      className="flex flex-col gap-2 rounded-lg border bg-surface-sunken p-3"
    >
      <h3 className="text-sm font-medium">Creating the project</h3>
      <ol className="flex flex-col gap-1.5">
        {job.steps.map((step) => {
          const look = LOOK[step.state];
          return (
            <li key={step.name} data-step={step.name} data-state={step.state}>
              <div
                className={cn(
                  "flex items-center gap-2 text-sm [&_svg]:size-4",
                  step.state === "pending" ? "text-ink-muted" : "text-ink",
                )}
              >
                <span className={look.tone}>{look.icon}</span>
                <span className="flex-1">{stepTitle(step, form, job)}</span>
                <span className={cn("text-xs", look.tone)}>{look.label}</span>
              </div>
              {step.state === "failed" ? (
                <div className="mt-2 ml-6 flex flex-col gap-2 text-sm">
                  <p role="alert" className="text-danger">
                    {step.message}
                  </p>
                  {step.output ? (
                    <pre className="max-h-48 overflow-auto rounded-md border bg-surface p-2 font-mono text-xs whitespace-pre-wrap">
                      {step.output}
                    </pre>
                  ) : null}
                  {rollback ? (
                    <p className="text-ink-muted">{rollback}</p>
                  ) : null}
                </div>
              ) : null}
            </li>
          );
        })}
      </ol>
      <p className="text-sm text-ink-muted">
        If a step fails, everything created so far is rolled back and you can
        fix the field.
      </p>
    </section>
  );
}
