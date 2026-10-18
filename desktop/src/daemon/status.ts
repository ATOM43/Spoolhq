import {
  DaemonError,
  fromCommandError,
  getDaemonInfo,
  getHealth,
  getVersion,
} from "@/api";

/** How often the app checks the daemon, in milliseconds. */
export const POLL_INTERVAL_MS = 3000;

/**
 * After the daemon was reachable, this many failed checks in a row (about 9 s) show
 * "Daemon not running" instead of "Reconnecting…".
 */
export const FAILURES_BEFORE_DOWN = 3;

/** The result of one check, plus what is needed to tell a blip from an outage. */
export type DaemonCheck =
  | { ok: true; version: string; port: number }
  | {
      ok: false;
      error: DaemonError;
      failures: number;
      everConnected: boolean;
    };

export type DaemonStatus =
  | { state: "ok"; version: string; port: number }
  | { state: "reconnecting" }
  | { state: "down"; port: number | null }
  | { state: "error"; error: DaemonError };

/** Check health (no token) first, so a stopped daemon reads as "not running". */
export async function checkDaemon(
  previous: DaemonCheck | undefined,
): Promise<DaemonCheck> {
  try {
    const info = await getDaemonInfo();
    await getHealth();
    const { version } = await getVersion();
    return { ok: true, version, port: info.port };
  } catch (error) {
    return {
      ok: false,
      error: fromCommandError(error),
      failures: previous && !previous.ok ? previous.failures + 1 : 1,
      everConnected: previous ? previous.ok || previous.everConnected : false,
    };
  }
}

export function deriveStatus(check: DaemonCheck | undefined): DaemonStatus {
  if (check === undefined) {
    return { state: "reconnecting" };
  }
  if (check.ok) {
    return { state: "ok", version: check.version, port: check.port };
  }
  const { detail } = check.error;
  if (detail.kind !== "not_running") {
    return { state: "error", error: check.error };
  }
  if (check.everConnected && check.failures < FAILURES_BEFORE_DOWN) {
    return { state: "reconnecting" };
  }
  return { state: "down", port: detail.port };
}
