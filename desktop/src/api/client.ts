/**
 * Typed client for the local daemon.
 *
 * Requests go through the Rust commands `daemon_info` and `daemon_get`, which add the
 * bearer token, so the token never reaches the webview. Every failure is thrown as a
 * {@link DaemonError}.
 */
import { invoke } from "@tauri-apps/api/core";

import { DaemonError } from "./errors";

export interface DaemonInfo {
  port: number;
  tokenPresent: boolean;
  tokenPath: string;
}

export interface Health {
  status: "ok";
}

export interface Version {
  version: string;
}

interface RawDaemonInfo {
  port: number;
  token_present: boolean;
  token_path: string;
}

interface DaemonReply {
  status: number;
  body: string;
}

/** The port the daemon should be on and whether a token file exists. */
export async function getDaemonInfo(): Promise<DaemonInfo> {
  const raw = await call<RawDaemonInfo>("daemon_info");
  return {
    port: raw.port,
    tokenPresent: raw.token_present,
    tokenPath: raw.token_path,
  };
}

/** `GET /api/health`: needs no token, so it tells whether the daemon is up. */
export async function getHealth(): Promise<Health> {
  const body = await get("/api/health", false);
  if (!isRecord(body) || body.status !== "ok") {
    throw invalid('expected {"status": "ok"}');
  }
  return { status: "ok" };
}

/** `GET /api/version`: needs the token. */
export async function getVersion(): Promise<Version> {
  const body = await get("/api/version", true);
  if (!isRecord(body) || typeof body.version !== "string") {
    throw invalid('expected {"version": "<string>"}');
  }
  return { version: body.version };
}

async function get(path: string, authenticated: boolean): Promise<unknown> {
  const reply = await call<DaemonReply>("daemon_get", { path, authenticated });
  if (reply.status === 401) {
    throw new DaemonError({ kind: "unauthorized" });
  }
  if (reply.status === 400) {
    throw new DaemonError({ kind: "bad_host" });
  }
  if (reply.status < 200 || reply.status >= 300) {
    throw new DaemonError({ kind: "http", status: reply.status });
  }
  try {
    return JSON.parse(reply.body) as unknown;
  } catch {
    throw invalid("the body is not JSON");
  }
}

async function call<T>(
  command: string,
  args?: Record<string, unknown>,
): Promise<T> {
  try {
    return await invoke<T>(command, args);
  } catch (error) {
    throw fromCommandError(error);
  }
}

/** Map a rejected `invoke` (a serialised Rust `DaemonError`, or anything else). */
export function fromCommandError(error: unknown): DaemonError {
  if (error instanceof DaemonError) {
    return error;
  }
  if (isRecord(error)) {
    switch (error.kind) {
      case "not_running":
        return new DaemonError({
          kind: "not_running",
          port: typeof error.port === "number" ? error.port : null,
          message: typeof error.message === "string" ? error.message : "",
        });
      case "token_missing":
        return new DaemonError({
          kind: "token_missing",
          tokenPath: typeof error.path === "string" ? error.path : "",
        });
      case "config":
        return new DaemonError({
          kind: "config",
          message: text(error.message),
        });
      case "invalid_request":
        return new DaemonError({
          kind: "internal",
          message: text(error.message),
        });
    }
  }
  return new DaemonError({
    kind: "internal",
    message: error instanceof Error ? error.message : text(error),
  });
}

function invalid(message: string): DaemonError {
  return new DaemonError({ kind: "invalid_response", message });
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function text(value: unknown): string {
  return typeof value === "string" ? value : String(value);
}
