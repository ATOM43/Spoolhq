import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, body, DaemonError, queryKeys, type Schemas } from "@/shared/api";

/** What the current dialog asks for; T36 replaces it with the full request. */
export interface CreateProject {
  name: string;
  repo: string;
  branch: string;
  template?: string;
}
export type CommandTestResult = Schemas["CommandTestResult"];
export type Gate = Schemas["CommandTest"]["gate"];
export const GATES: readonly Gate[] = ["install", "lint", "test"];

export function useTemplates() {
  return useQuery({
    queryKey: queryKeys.templates,
    queryFn: () => body(api.GET("/api/templates")),
    retry: false,
  });
}

const PLACEHOLDERS = {
  install: "just install",
  lint: "just lint",
  test: "just test",
};
// shortcut: polls every 500 ms while the job runs (DECISIONS 340); T36 shows the steps.
const POLL_MS = 500;

/** Start the creation job and wait for it; a failed step throws its message. */
async function createProject(
  project: CreateProject,
): Promise<{ name: string }> {
  const { job_id } = await body(
    api.POST("/api/projects", {
      body: {
        name: project.name,
        source: project.template ? "template" : "existing",
        repo_path: project.repo,
        template: project.template ?? null,
        commands: PLACEHOLDERS,
        merge_preset: "direct_unless_risky",
      },
    }),
  );
  for (;;) {
    const job = await body(
      api.GET("/api/jobs/{job_id}", { params: { path: { job_id } } }),
    );
    if (job.state === "succeeded") {
      return { name: job.project };
    }
    if (job.state !== "running") {
      const failed = job.steps.find((step) => step.state === "failed");
      throw new Error(
        [failed?.message ?? `Creation ${job.state}`, failed?.output]
          .filter(Boolean)
          .join(": "),
      );
    }
    await new Promise((resolve) => setTimeout(resolve, POLL_MS));
  }
}

/** `POST /api/projects`; on success the project list refetches, so Home shows it. */
export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createProject,
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.projects }),
  });
}

export interface ProjectSettings {
  settings: Record<string, unknown>;
  etag: string;
}

export async function loadSettings(name: string): Promise<ProjectSettings> {
  const { data, response } = await api.GET("/api/projects/{name}/settings", {
    params: { path: { name } },
  });
  return {
    settings: data?.settings ?? {},
    etag: response.headers.get("ETag") ?? "",
  };
}

export function useProjectSettings(name: string) {
  return useQuery({
    // Not under ["projects"], so run events don't refetch it while it is edited.
    queryKey: ["project-settings", name],
    queryFn: () => loadSettings(name),
    retry: false,
    staleTime: Infinity,
  });
}

/** Save the three stack commands into `project.yaml`, with the ETag from the load. */
export async function saveCommands(
  name: string,
  loaded: ProjectSettings,
  commands: Record<Gate, string>,
): Promise<void> {
  const current = loaded.settings.commands;
  const others = typeof current === "object" && current !== null ? current : {};
  await api.PUT("/api/projects/{name}/settings", {
    params: { path: { name }, header: { "if-match": loaded.etag } },
    body: {
      settings: { ...loaded.settings, commands: { ...others, ...commands } },
    },
  });
}

export function testCommand(
  name: string,
  gate: Gate,
  command: string,
): Promise<CommandTestResult> {
  return body(
    api.POST("/api/projects/{name}/commands/test", {
      params: { path: { name } },
      body: { gate, command },
    }),
  );
}

/** An API error's field (`name`, `body.repo` or `repo_path` → `repo`) and message. */
export function fieldError(
  error: unknown,
): { field: string; message: string } | null {
  if (error instanceof DaemonError && error.detail.kind === "api") {
    const { field, message } = error.detail;
    if (field !== null) {
      const name = field.replace(/^body\./, "");
      return { field: name === "repo_path" ? "repo" : name, message };
    }
  }
  return null;
}
