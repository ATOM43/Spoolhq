import { useQuery } from "@tanstack/react-query";

import { api, body, queryKeys, type Schemas } from "@/shared/api";

export type ProjectSummary = Schemas["ProjectSummary"];
export type ProjectDetail = Schemas["ProjectDetail"];

/** Every project with its progress and run state. Kept fresh by `useProjectEvents`. */
export function useProjects({ enabled = true }: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: queryKeys.projects,
    queryFn: () => body(api.GET("/api/projects")),
    enabled,
    retry: false,
  });
}

export function useProject(name: string) {
  return useQuery({
    queryKey: queryKeys.project(name),
    queryFn: () =>
      body(api.GET("/api/projects/{name}", { params: { path: { name } } })),
    retry: false,
  });
}
