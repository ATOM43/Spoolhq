import { useQuery } from "@tanstack/react-query";

import { api, queryKeys } from "@/shared/api";

/** `project.yaml` as data (only what the file sets), with its ETag. */
export interface SettingsFile {
  settings: Record<string, unknown>;
  etag: string;
}

export async function loadSettings(name: string): Promise<SettingsFile> {
  const { data, response } = await api.GET("/api/projects/{name}/settings", {
    params: { path: { name } },
  });
  return {
    settings: data?.settings ?? {},
    etag: response.headers.get("ETag") ?? "",
  };
}

/** `PUT …/settings` with `If-Match`; resolves to the new file, rejects 412 or 422. */
export async function saveSettings(
  name: string,
  settings: Record<string, unknown>,
  etag: string,
): Promise<SettingsFile> {
  const { data, response } = await api.PUT("/api/projects/{name}/settings", {
    params: { path: { name }, header: { "if-match": etag } },
    body: { settings },
  });
  return {
    settings: data?.settings ?? settings,
    etag: response.headers.get("ETag") ?? "",
  };
}

/** The settings as last loaded; the Settings tab owns its edits, so no refetch on focus. */
export function useProjectSettings(name: string) {
  return useQuery({
    queryKey: queryKeys.projectSettings(name),
    queryFn: () => loadSettings(name),
    retry: false,
    staleTime: Infinity,
  });
}
