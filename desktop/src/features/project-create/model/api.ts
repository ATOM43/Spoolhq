import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, body, DaemonError, queryKeys, type Schemas } from "@/shared/api";

export type CreateProject = Schemas["CreateProject"];
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

/** `POST /api/projects`; on success the project list refetches, so Home shows it. */
export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (project: CreateProject) =>
      body(api.POST("/api/projects", { body: project })),
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

/** An API error's field (`name`, `body.repo` → `repo`) and message, if it has one. */
export function fieldError(
  error: unknown,
): { field: string; message: string } | null {
  if (error instanceof DaemonError && error.detail.kind === "api") {
    const { field, message } = error.detail;
    if (field !== null) {
      return { field: field.replace(/^body\./, ""), message };
    }
  }
  return null;
}
