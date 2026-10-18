import { invoke } from "@tauri-apps/api/core";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getDaemonInfo, getHealth, getVersion } from "./client";
import { DaemonError, type DaemonErrorDetail } from "./errors";

vi.mock("@tauri-apps/api/core", () => ({ invoke: vi.fn() }));

const invokeMock = vi.mocked(invoke);

function reply(status: number, body: string): void {
  invokeMock.mockResolvedValueOnce({ status, body });
}

async function failure(promise: Promise<unknown>): Promise<DaemonErrorDetail> {
  const error: unknown = await promise.then(
    () => {
      throw new Error("expected the call to fail");
    },
    (reason: unknown) => reason,
  );
  expect(error).toBeInstanceOf(DaemonError);
  return (error as DaemonError).detail;
}

describe("daemon client", () => {
  beforeEach(() => {
    invokeMock.mockReset();
  });

  it("returns health and calls it without the token", async () => {
    reply(200, '{"status":"ok"}');
    await expect(getHealth()).resolves.toEqual({ status: "ok" });
    expect(invokeMock).toHaveBeenCalledWith("daemon_get", {
      path: "/api/health",
      authenticated: false,
    });
  });

  it("returns the version and asks Rust to add the token", async () => {
    reply(200, '{"version":"0.1.0"}');
    await expect(getVersion()).resolves.toEqual({ version: "0.1.0" });
    expect(invokeMock).toHaveBeenCalledWith("daemon_get", {
      path: "/api/version",
      authenticated: true,
    });
  });

  it("maps connection refused to not_running", async () => {
    invokeMock.mockRejectedValueOnce({
      kind: "not_running",
      port: 8765,
      message: "error sending request",
    });
    expect(await failure(getHealth())).toEqual({
      kind: "not_running",
      port: 8765,
      message: "error sending request",
    });
  });

  it("maps a missing token file to token_missing with its path", async () => {
    invokeMock.mockRejectedValueOnce({
      kind: "token_missing",
      path: "/home/me/.spoolhq/token",
    });
    expect(await failure(getVersion())).toEqual({
      kind: "token_missing",
      tokenPath: "/home/me/.spoolhq/token",
    });
  });

  it("maps 401 to unauthorized", async () => {
    reply(401, '{"detail":"missing or invalid token"}');
    expect(await failure(getVersion())).toEqual({ kind: "unauthorized" });
  });

  it("maps 400 to bad_host", async () => {
    reply(400, '{"detail":"invalid Host header"}');
    expect(await failure(getHealth())).toEqual({ kind: "bad_host" });
  });

  it("maps other error statuses to http", async () => {
    reply(503, "unavailable");
    expect(await failure(getHealth())).toEqual({ kind: "http", status: 503 });
  });

  it("maps a body that is not JSON to invalid_response", async () => {
    reply(200, "<html>not json</html>");
    expect((await failure(getHealth())).kind).toBe("invalid_response");
  });

  it("maps JSON of the wrong shape to invalid_response", async () => {
    reply(200, '{"version":42}');
    expect((await failure(getVersion())).kind).toBe("invalid_response");
    reply(200, "[]");
    expect((await failure(getHealth())).kind).toBe("invalid_response");
  });

  it("maps config errors and unknown bridge failures", async () => {
    invokeMock.mockRejectedValueOnce({ kind: "config", message: "bad port" });
    expect(await failure(getDaemonInfo())).toEqual({
      kind: "config",
      message: "bad port",
    });
    invokeMock.mockRejectedValueOnce(new TypeError("no Tauri here"));
    expect(await failure(getHealth())).toEqual({
      kind: "internal",
      message: "no Tauri here",
    });
  });

  it("converts daemon_info to camelCase", async () => {
    invokeMock.mockResolvedValueOnce({
      port: 9001,
      token_present: true,
      token_path: "/x/token",
    });
    await expect(getDaemonInfo()).resolves.toEqual({
      port: 9001,
      tokenPresent: true,
      tokenPath: "/x/token",
    });
    expect(invokeMock).toHaveBeenCalledWith("daemon_info", undefined);
  });
});
