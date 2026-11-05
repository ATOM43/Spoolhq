import {
  CircleCheck,
  CircleDashed,
  CirclePause,
  CircleX,
  FilePen,
  FileText,
  Hand,
  LoaderCircle,
  Moon,
} from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/shared/lib";

import type { ProjectSummary } from "../model/queries";
import { projectState, type ProjectStatusKind } from "../model/status";

const LOOK: Record<ProjectStatusKind, { icon: ReactNode; tone: string }> = {
  settings_invalid: {
    icon: <CircleX aria-hidden />,
    tone: "bg-danger/10 text-danger",
  },
  running: {
    icon: <LoaderCircle aria-hidden className="animate-spin" />,
    tone: "bg-accent/10 text-accent",
  },
  paused_limit: {
    icon: <CirclePause aria-hidden />,
    tone: "bg-warning/10 text-warning",
  },
  paused: {
    icon: <CirclePause aria-hidden />,
    tone: "bg-warning/10 text-warning",
  },
  needs_you: { icon: <Hand aria-hidden />, tone: "bg-warning/10 text-warning" },
  no_spec: {
    icon: <FilePen aria-hidden />,
    tone: "bg-surface-sunken text-ink-muted",
  },
  no_plan: {
    icon: <FileText aria-hidden />,
    tone: "bg-surface-sunken text-ink-muted",
  },
  plan_draft: {
    icon: <CircleDashed aria-hidden />,
    tone: "bg-surface-sunken text-ink-muted",
  },
  all_done: {
    icon: <CircleCheck aria-hidden />,
    tone: "bg-success/10 text-success",
  },
  idle: {
    icon: <Moon aria-hidden />,
    tone: "bg-surface-sunken text-ink-muted",
  },
};

/** Status as an icon + label chip, never colour alone. */
export function ProjectStatus({ project }: { project: ProjectSummary }) {
  const { kind, label } = projectState(project);
  const { icon, tone } = LOOK[kind];
  return (
    <span
      data-status={kind}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-1.5 py-0.5 text-sm font-medium [&_svg]:size-3.5",
        tone,
      )}
    >
      {icon}
      {label}
    </span>
  );
}
