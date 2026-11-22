import {
  DaemonError,
  fromCommandError,
  getDaemonInfo,
  getHealth,
  getVersion,
  type LaunchState,
} from "@/shared/api";

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
      /** What the app did at launch; null when `daemon_info` itself failed. */
      launch: LaunchState | null;
    };

export type DaemonStatus =
  | { state: "ok"; version: string; port: number }
  | { state: "reconnecting" }
  | { state: "starting" }
  | { state: "port_in_use"; port: number; configPath: string }
  /** `logDir` is set when the app started its own daemon and it did not answer. */
  | { state: "down"; port: number | null; logDir: string | null }
  | { state: "error"; error: DaemonError };

/** Check health (no token) first, so a stopped daemon reads as "not running". */
export async function checkDaemon(
  previous: DaemonCheck | undefined,
): Promise<DaemonCheck> {
  let launch: LaunchState | null = null;
  try {
    const info = await getDaemonInfo();
    launch = info.launch;
    await getHealth();
    const { version } = await getVersion();
    return { ok: true, version, port: info.port };
  } catch (error) {
    return {
      ok: false,
      error: fromCommandError(error),
      failures: previous && !previous.ok ? previous.failures + 1 : 1,
      everConnected: previous ? previous.ok || previous.everConnected : false,
      launch,
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
  const { launch } = check;
  if (launch?.state === "port_in_use") {
    return {
      state: "port_in_use",
      port: launch.port,
      configPath: launch.configPath,
    };
  }
  if (launch?.state === "checking" || launch?.state === "starting") {
    return { state: "starting" };
  }
  const { detail } = check.error;
  if (detail.kind !== "not_running") {
    return { state: "error", error: check.error };
  }
  if (check.everConnected && check.failures < FAILURES_BEFORE_DOWN) {
    return { state: "reconnecting" };
  }
  const logDir = launch?.state === "failed" ? launch.logDir : null;
  return { state: "down", port: detail.port, logDir };
}
