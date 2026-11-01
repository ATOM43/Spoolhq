import { invoke } from "@tauri-apps/api/core";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DaemonError } from "./errors";
import { api } from "./http";

vi.mock("@tauri-apps/api/core", () => ({ invoke: vi.fn() }));

const invokeMock = vi.mocked(invoke);

async function rejection(promise: Promise<unknown>): Promise<DaemonError> {
  const error: unknown = await promise.then(
    () => {
      throw new Error("expected the call to fail");
    },
    (reason: unknown) => reason,
  );
  expect(error).toBeInstanceOf(DaemonError);
  return error as DaemonError;
}

describe("API client", () => {
  beforeEach(() => {
    invokeMock.mockReset();
  });

  it("sends the method, path, query and body through daemon_request", async () => {
    invokeMock.mockResolvedValueOnce({
      status: 200,
      body: '{"items":[],"next_cursor":null}',
      etag: null,
    });
    const { data } = await api.GET("/api/projects/{name}/runs", {
      params: { path: { name: "demo" }, query: { limit: 10, cursor: "a=b" } },
    });
    expect(data).toEqual({ items: [], next_cursor: null });
    expect(invokeMock).toHaveBeenCalledWith("daemon_request", {
      method: "GET",
      path: "/api/projects/demo/runs?limit=10&cursor=a%3Db",
      body: null,
      ifMatch: null,
    });
  });

  it("passes If-Match and returns the new ETag", async () => {
    invokeMock.mockResolvedValueOnce({
      status: 200,
      body: '{"content":"# Spec"}',
      etag: '"new"',
    });
    const { data, response } = await api.PUT("/api/projects/{name}/spec", {
      params: { path: { name: "demo" }, header: { "if-match": '"old"' } },
      body: { content: "# Spec" },
    });
    expect(data).toEqual({ content: "# Spec" });
    expect(response.headers.get("ETag")).toBe('"new"');
    expect(invokeMock).toHaveBeenCalledWith("daemon_request", {
      method: "PUT",
      path: "/api/projects/demo/spec",
      body: '{"content":"# Spec"}',
      ifMatch: '"old"',
    });
  });

  it("turns a 412 into an error carrying the current ETag and content", async () => {
    invokeMock.mockResolvedValueOnce({
      status: 412,
      body: JSON.stringify({
        error: {
          code: "edit_conflict",
          message: "the file changed since you loaded it",
          etag: '"current"',
          current: { content: "theirs" },
        },
      }),
    });
    const error = await rejection(
      api.PUT("/api/projects/{name}/spec", {
        params: { path: { name: "demo" }, header: { "if-match": '"stale"' } },
        body: { content: "mine" },
      }),
    );
    expect(error.detail).toEqual({
      kind: "api",
      status: 412,
      code: "edit_conflict",
      message: "the file changed since you loaded it",
      field: null,
      etag: '"current"',
      current: { content: "theirs" },
    });
    expect(error.message).toBe("the file changed since you loaded it");
  });

  it("maps a missing daemon and other statuses like the other calls", async () => {
    invokeMock.mockRejectedValueOnce({
      kind: "not_running",
      port: 8765,
      message: "refused",
    });
    expect((await rejection(api.GET("/api/projects"))).kind).toBe(
      "not_running",
    );
    invokeMock.mockResolvedValueOnce({ status: 401, body: "{}" });
    expect((await rejection(api.GET("/api/projects"))).kind).toBe(
      "unauthorized",
    );
    invokeMock.mockResolvedValueOnce({ status: 502, body: "bad gateway" });
    expect((await rejection(api.GET("/api/projects"))).detail).toEqual({
      kind: "http",
      status: 502,
    });
  });

  it("handles 204 without a body", async () => {
    invokeMock.mockResolvedValueOnce({ status: 204, body: "" });
    const { response } = await api.DELETE("/api/settings/secrets/{secret}", {
      params: { path: { secret: "github" } },
    });
    expect(response.status).toBe(204);
  });
});
