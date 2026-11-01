import { useQuery } from "@tanstack/react-query";

import { api, queryKeys } from "@/shared/api";

export const SPEC_FILE = "CONTEXT.md";

export interface SpecFile {
  content: string;
  etag: string;
}

export async function loadSpec(name: string): Promise<SpecFile> {
  const { data, response } = await api.GET("/api/projects/{name}/spec", {
    params: { path: { name } },
  });
  return {
    content: data?.content ?? "",
    etag: response.headers.get("ETag") ?? "",
  };
}

/** `PUT …/spec` with `If-Match`; resolves to the new ETag, rejects 412 on a conflict. */
export async function saveSpec(
  name: string,
  content: string,
  etag: string,
): Promise<string> {
  const { response } = await api.PUT("/api/projects/{name}/spec", {
    params: { path: { name }, header: { "if-match": etag } },
    body: { content },
  });
  return response.headers.get("ETag") ?? "";
}

/** The spec as last loaded; the editor owns it after that, so it never refetches. */
export function useSpec(name: string) {
  return useQuery({
    queryKey: queryKeys.spec(name),
    queryFn: () => loadSpec(name),
    retry: false,
    staleTime: Infinity,
  });
}
