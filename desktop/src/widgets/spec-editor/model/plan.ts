import type { ProjectDetail } from "@/entities/project";
import type { CurrentRun } from "@/entities/run";

import type { SaveState } from "./autosave";

export interface PlanState {
  planning: boolean;
  /** The latest plan run failed: the planner's reason. */
  failure: string | null;
  /** The last progress line the planner reported. */
  progress: string | null;
}

export function planState(run: CurrentRun | undefined): PlanState {
  const latest = run?.run;
  if (latest?.kind !== "plan") {
    return { planning: false, failure: null, progress: null };
  }
  return {
    planning: latest.status === "running",
    failure:
      latest.status === "blocked"
        ? (latest.reason ?? "the planner stopped")
        : null,
    progress: run?.phases.at(-1)?.text ?? null,
  };
}

/** Why Generate plan can't start now, or null. */
export function planBlocker(
  project: ProjectDetail,
  spec: string,
  save: SaveState,
): string | null {
  if (spec.trim() === "") {
    return "Write at least an objective first";
  }
  if (project.idle?.code === "plan_not_approved") {
    return "A draft plan exists: review and approve it in the Tickets tab";
  }
  if (save === "conflict") {
    return "Choose Reload or Keep mine first: CONTEXT.md changed on disk";
  }
  if (save !== "saved") {
    return "Save the spec first: press Ctrl+S or wait a second";
  }
  return null;
}
