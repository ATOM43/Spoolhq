import { describe, expect, it } from "vitest";

import { DaemonError, type LaunchState } from "@/shared/api";

import { deriveStatus, type DaemonCheck } from "./status";

const notRunning = new DaemonError({
  kind: "not_running",
  port: 8765,
  message: "connection refused",
});

function failed(
  failures: number,
  everConnected: boolean,
  launch: LaunchState | null = { state: "external" },
): DaemonCheck {
  return { ok: false, error: notRunning, failures, everConnected, launch };
}

describe("deriveStatus", () => {
  it("is reconnecting before the first check finishes", () => {
    expect(deriveStatus(undefined)).toEqual({ state: "reconnecting" });
  });

  it("is ok with the daemon's version", () => {
    expect(deriveStatus({ ok: true, version: "0.1.0", port: 8765 })).toEqual({
      state: "ok",
      version: "0.1.0",
      port: 8765,
    });
  });

  it("is down at once if the daemon was never reachable", () => {
    expect(deriveStatus(failed(1, false))).toEqual({
      state: "down",
      port: 8765,
      logDir: null,
    });
  });

  it("is starting while the app checks the port or starts its daemon", () => {
    expect(deriveStatus(failed(1, false, { state: "checking" }))).toEqual({
      state: "starting",
    });
    expect(deriveStatus(failed(4, false, { state: "starting" }))).toEqual({
      state: "starting",
    });
  });

  it("reports another program on the port, whatever it answers", () => {
    const port = { state: "port_in_use", port: 8765, configPath: "/h/c.toml" };
    const error = new DaemonError({ kind: "http", status: 404 });
    expect(
      deriveStatus({
        ok: false,
        error,
        failures: 1,
        everConnected: false,
        launch: port as LaunchState,
      }),
    ).toEqual(port);
  });

  it("is down with the log folder when the app's daemon did not answer", () => {
    const launch: LaunchState = {
      state: "failed",
      logDir: "/h/logs",
      message: "no answer within 15 s",
    };
    expect(deriveStatus(failed(1, false, launch))).toEqual({
      state: "down",
      port: 8765,
      logDir: "/h/logs",
    });
  });

  it("reconnects after losing a daemon, then gives up", () => {
    expect(deriveStatus(failed(1, true)).state).toBe("reconnecting");
    expect(deriveStatus(failed(2, true)).state).toBe("reconnecting");
    expect(deriveStatus(failed(3, true)).state).toBe("down");
  });

  it("reports other failures as errors", () => {
    const error = new DaemonError({ kind: "unauthorized" });
    expect(
      deriveStatus({
        ok: false,
        error,
        failures: 1,
        everConnected: true,
        launch: null,
      }),
    ).toEqual({ state: "error", error });
  });
});
