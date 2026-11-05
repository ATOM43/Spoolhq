import { useQuery } from "@tanstack/react-query";

import { api, body, DaemonError, queryKeys, type Schemas } from "@/shared/api";

export type CreateRequest = Schemas["CreateProject"];
export type Job = Schemas["JobView"];
export type JobStep = Schemas["StepView"];
export type Template = Schemas["TemplateView"];

/** While a job runs (DECISIONS 340). */
export const POLL_MS = 500;

export function useTemplates() {
  return useQuery({
    queryKey: queryKeys.templates,
    queryFn: () => body(api.GET("/api/templates")),
    retry: false,
  });
}

/** The daemon's projects folder, for the Workspace line. */
export function useProjectsDir() {
  return useQuery({
    queryKey: queryKeys.settings,
    queryFn: () => body(api.GET("/api/settings")),
    retry: false,
    select: (settings) => settings.projects_dir,
  });
}

/** `GET /api/jobs/{id}` every 500 ms while it runs; polling stops with the component. */
export function useJob(id: string | null) {
  return useQuery({
    queryKey: queryKeys.job(id ?? ""),
    queryFn: () =>
      body(
        api.GET("/api/jobs/{job_id}", {
          params: { path: { job_id: id ?? "" } },
        }),
      ),
    enabled: id !== null,
    refetchInterval: (query) =>
      query.state.data?.state === "running" ? POLL_MS : false,
  });
}

export async function startJob(request: CreateRequest): Promise<string> {
  const started = await body(api.POST("/api/projects", { body: request }));
  return started.job_id;
}

export function cancelJob(id: string): Promise<Job> {
  return body(
    api.POST("/api/jobs/{job_id}/cancel", { params: { path: { job_id: id } } }),
  );
}

/** A 422's request field (`body.` dropped) and message; null for any other error. */
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
