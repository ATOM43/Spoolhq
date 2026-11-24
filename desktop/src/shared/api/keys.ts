/**
 * TanStack Query keys for daemon data, in one place so the event bridge can invalidate
 * a project's runs and tickets without importing those slices.
 */
export const queryKeys = {
  projects: ["projects"] as const,
  project: (name: string) => ["projects", name] as const,
  tickets: (project: string) => ["tickets", project] as const,
  // Under the tickets' key: invalidating a project's tickets refreshes these too.
  plan: (project: string) => ["tickets", project, "plan"] as const,
  ticket: (project: string, id: string) =>
    ["tickets", project, "detail", id] as const,
  review: (project: string, runId: number) =>
    ["tickets", project, "review", runId] as const,
  runs: (project: string) => ["runs", project] as const,
  agents: ["agents"] as const,
  settings: ["settings"] as const,
  version: ["version"] as const,
  // Not under ["projects"], so run events don't refetch the spec while it is edited.
  spec: (project: string) => ["spec", project] as const,
  // Not under ["projects"] either, so run events don't reset the Settings tab's form.
  projectSettings: (project: string) => ["project-settings", project] as const,
  // Polled on its own (sync runs outside ticket runs), so not under ["projects"].
  tracker: (project: string) => ["tracker", project] as const,
  templates: ["templates"] as const,
  // Rust's update state, not the daemon's.
  update: ["update"] as const,
  job: (id: string) => ["jobs", id] as const,
  draftJob: (project: string, id: string) =>
    ["draft-jobs", project, id] as const,
};
