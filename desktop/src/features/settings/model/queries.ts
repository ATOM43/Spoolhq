import { useQuery, useQueryClient } from "@tanstack/react-query";

import { api, body, getVersion, queryKeys, type Schemas } from "@/shared/api";

export type DaemonSettings = Schemas["DaemonSettings"];
export type SecretName = "anthropic" | "github" | "clickup";
type Agents = Schemas["AgentsView"];

export function useDaemonSettings() {
  return useQuery({
    queryKey: queryKeys.settings,
    queryFn: () => body(api.GET("/api/settings")),
    retry: false,
  });
}

export function useVersion() {
  return useQuery({
    queryKey: queryKeys.version,
    queryFn: getVersion,
    retry: false,
  });
}

/**
 * Store a secret in the OS keychain. A plain call, not a mutation, so the value is never
 * kept in TanStack's mutation cache; the caller drops it once this resolves.
 */
export async function storeSecret(name: SecretName, value: string) {
  await api.PUT("/api/settings/secrets/{secret}", {
    params: { path: { secret: name } },
    body: { value },
  });
}

export async function removeSecret(name: SecretName) {
  await api.DELETE("/api/settings/secrets/{secret}", {
    params: { path: { secret: name } },
  });
}

/** Refetch what a secret changes: its status, and whether the Agent SDK is ready. */
export function useRefreshSecrets() {
  const queryClient = useQueryClient();
  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.settings }),
      queryClient.invalidateQueries({ queryKey: queryKeys.agents }),
    ]);
}

/** A backend can run: a logged-in coding CLI, or a saved Anthropic API key. */
export function backendReady(
  agents: Agents | undefined,
  settings: DaemonSettings | undefined,
): boolean {
  const cli = agents?.backends.some((b) => b.installed && b.logged_in) ?? false;
  return cli || (settings?.secrets.anthropic?.set ?? false);
}
