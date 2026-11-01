import {
  CircleAlert,
  CircleCheck,
  CircleDashed,
  CircleHelp,
  CirclePause,
  FileText,
  LoaderCircle,
} from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/shared/lib";

import type { ProjectSummary } from "../model/queries";

interface Look {
  icon: ReactNode;
  label: string;
  tone: string;
}

/** The project's state in a word, most urgent first. */
function describeProject(project: ProjectSummary): Look {
  if (project.run_state === "running") {
    return {
      icon: <LoaderCircle aria-hidden className="animate-spin" />,
      label: "Running",
      tone: "text-accent",
    };
  }
  if (project.run_state === "paused") {
    return {
      icon: <CirclePause aria-hidden />,
      label: "Paused",
      tone: "text-warning",
    };
  }
  if (project.needs_you > 0) {
    return {
      icon: <CircleAlert aria-hidden />,
      label: "Needs you",
      tone: "text-warning",
    };
  }
  if (project.run_state === "unknown") {
    return {
      icon: <CircleHelp aria-hidden />,
      label: "Unknown",
      tone: "text-ink-muted",
    };
  }
  if (project.total === 0) {
    return {
      icon: <FileText aria-hidden />,
      label: "No plan yet",
      tone: "text-ink-muted",
    };
  }
  if (project.done === project.total) {
    return {
      icon: <CircleCheck aria-hidden />,
      label: "Done",
      tone: "text-success",
    };
  }
  return {
    icon: <CircleDashed aria-hidden />,
    label: "Idle",
    tone: "text-ink-muted",
  };
}

/** Status as icon + label, never colour alone. */
export function ProjectStatus({ project }: { project: ProjectSummary }) {
  const { icon, label, tone } = describeProject(project);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-sm [&_svg]:size-4",
        tone,
      )}
    >
      {icon}
      <span className="text-ink">{label}</span>
    </span>
  );
}
