import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAgents } from "@/entities/agent";
import { useCheckNow } from "@/entities/update";

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

type Desktop = DaemonSettings["desktop"];

/**
 * Save `[desktop]` keys to `~/.spoolhq/config.toml`, where the app reads them (keys left
 * out keep their value). After `check_updates` changes, Rust checks again: with checks
 * off that makes no request.
 */
export function useSaveDesktop() {
  const queryClient = useQueryClient();
  const checkNow = useCheckNow();
  return useMutation({
    mutationFn: (change: Partial<Desktop>) => {
      const current = queryClient.getQueryData<DaemonSettings>(
        queryKeys.settings,
      )?.desktop;
      const desktop = {
        keep_running: true,
        check_updates: true,
        ...current,
        ...change,
      };
      return body(api.PUT("/api/settings/desktop", { body: desktop }));
    },
    onSuccess: (desktop, change) => {
      queryClient.setQueryData<DaemonSettings>(queryKeys.settings, (old) =>
        old ? { ...old, desktop } : old,
      );
      if (change.check_updates !== undefined) {
        checkNow.mutate();
      }
    },
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

/** Ask the daemon to try a stored secret against its provider. The value stays there. */
export function testSecret(name: SecretName) {
  return body(
    api.POST("/api/settings/secrets/{secret}/test", {
      params: { path: { secret: name } },
    }),
  );
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

/** A backend can run: a logged-in coding CLI, a saved Anthropic API key, or the dev
 * fake runner. */
export function backendReady(
  agents: Agents | undefined,
  settings: DaemonSettings | undefined,
): boolean {
  if (agents?.fake_runner) {
    return true;
  }
  const cli = agents?.backends.some((b) => b.installed && b.logged_in) ?? false;
  return cli || (settings?.secrets.anthropic?.set ?? false);
}

export const SET_UP_FIRST =
  "Set up an agent first: log in to a coding CLI or add an API key";

/** SET_UP_FIRST once the daemon has said no backend is ready; null otherwise. */
export function useAgentBlocker(): string | null {
  const agents = useAgents();
  const settings = useDaemonSettings();
  const known = agents.isSuccess && settings.isSuccess;
  return known && !backendReady(agents.data, settings.data)
    ? SET_UP_FIRST
    : null;
}
