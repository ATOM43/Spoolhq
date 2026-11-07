import {
  CircleCheck,
  CircleDashed,
  CircleMinus,
  CircleX,
  LoaderCircle,
} from "lucide-react";

import { cn } from "@/shared/lib";

import { STEPS, type Step, type StepState } from "../model/transcript";

const LABEL: Record<Step, string> = {
  worktree: "Worktree",
  implement: "Implement",
  gates: "Gates",
  review: "Review",
  policy: "Policy",
  integrate: "Integrate",
};

const LOOK: Record<StepState, { icon: typeof CircleCheck; className: string }> =
  {
    pending: { icon: CircleDashed, className: "text-ink-muted" },
    running: {
      icon: LoaderCircle,
      className: "text-accent [&_svg]:motion-safe:animate-spin",
    },
    passed: { icon: CircleCheck, className: "text-success" },
    failed: { icon: CircleX, className: "text-danger" },
    skipped: { icon: CircleMinus, className: "text-ink-muted opacity-60" },
  };

/** Worktree → Implement → Gates → Review → Policy → Integrate, each icon + label. */
export function StepIndicator({ states }: { states: Record<Step, StepState> }) {
  return (
    <ol
      aria-label="Steps"
      className="flex flex-wrap items-center gap-1 text-sm"
    >
      {STEPS.map((step, index) => {
        const state = states[step];
        const { icon: Icon, className } = LOOK[state];
        return (
          <li
            key={step}
            data-state={state}
            className={cn(
              "flex items-center gap-1",
              className,
              state === "running" && "font-medium motion-safe:animate-pulse",
            )}
          >
            {index > 0 ? (
              <span aria-hidden className="mx-1 h-px w-4 bg-border" />
            ) : null}
            <Icon aria-hidden className="size-4" />
            {LABEL[step]}
            <span className="sr-only">: {state}</span>
          </li>
        );
      })}
    </ol>
  );
}
