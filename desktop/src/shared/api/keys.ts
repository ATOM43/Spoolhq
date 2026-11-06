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
  review: (project: string, runId: number) =>
    ["tickets", project, "review", runId] as const,
  runs: (project: string) => ["runs", project] as const,
  agents: ["agents"] as const,
  settings: ["settings"] as const,
  version: ["version"] as const,
  // Not under ["projects"], so run events don't refetch the spec while it is edited.
  spec: (project: string) => ["spec", project] as const,
  templates: ["templates"] as const,
  job: (id: string) => ["jobs", id] as const,
};
