import { describe, expect, it } from "vitest";

import { DaemonError } from "@/api";

import { deriveStatus, type DaemonCheck } from "./status";

const notRunning = new DaemonError({
  kind: "not_running",
  port: 8765,
  message: "connection refused",
});

function failed(failures: number, everConnected: boolean): DaemonCheck {
  return { ok: false, error: notRunning, failures, everConnected };
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
      deriveStatus({ ok: false, error, failures: 1, everConnected: true }),
    ).toEqual({ state: "error", error });
  });
});
