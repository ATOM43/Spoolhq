import type { ProjectSummary } from "./queries";

export type ProjectStatusKind =
  | "creating"
  | "settings_invalid"
  | "running"
  | "paused_limit"
  | "paused"
  | "needs_you"
  | "no_spec"
  | "no_plan"
  | "plan_draft"
  | "all_done"
  | "idle";

export interface ProjectState {
  kind: ProjectStatusKind;
  label: string;
}

const capitalize = (text: string) =>
  text.charAt(0).toUpperCase() + text.slice(1);

/** `project.yaml: <field>: <message>`, the line Home and the panel show. */
export function settingsErrorLine(project: ProjectSummary): string | null {
  const problem = project.settings_error;
  if (!problem) {
    return null;
  }
  return problem.field
    ? `project.yaml: ${problem.field}: ${problem.message}`
    : `project.yaml: ${problem.message}`;
}

/** The project's state in a few words, most urgent first. Never "unknown". */
export function projectState(project: ProjectSummary): ProjectState {
  const run = project.run;
  if (project.run_state === "creating") {
    // A creation job holds it; its project.yaml is half written, so it isn't read.
    return { kind: "creating", label: "Creating…" };
  }
  if (project.settings_error) {
    return { kind: "settings_invalid", label: "Settings invalid" };
  }
  if (project.run_state === "running") {
    const step = project.run_step ? ` · ${capitalize(project.run_step)}` : "";
    return {
      kind: "running",
      label: `Running ${run?.ticket_id ?? "a ticket"}${step}`,
    };
  }
  if (project.run_state === "paused") {
    return run?.reset_at
      ? { kind: "paused_limit", label: "Paused · usage limit" }
      : { kind: "paused", label: "Paused" };
  }
  if (project.needs_you > 0) {
    return {
      kind: "needs_you",
      label: `Needs you (${String(project.needs_you)})`,
    };
  }
  if (project.total === 0) {
    return project.has_spec
      ? { kind: "no_plan", label: "No plan yet" }
      : { kind: "no_spec", label: "No spec yet" };
  }
  if (project.draft > 0) {
    return { kind: "plan_draft", label: "Plan in draft" };
  }
  if (project.done === project.total) {
    return { kind: "all_done", label: "All done" };
  }
  return { kind: "idle", label: "Idle" };
}
