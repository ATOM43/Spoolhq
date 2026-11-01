import { invoke } from "@tauri-apps/api/core";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { subscribeEvents, type EventEnvelope } from "./events";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: vi.fn(),
  Channel: class {
    onmessage: (message: unknown) => void = () => undefined;
  },
}));

const invokeMock = vi.mocked(invoke);

interface FakeChannel {
  onmessage: (message: unknown) => void;
}

function envelope(seq: number): EventEnvelope {
  return {
    seq,
    run_id: 1,
    attempt: null,
    ticket: "T01",
    type: "run.status",
    ts: "",
    data: {},
  };
}

/** The channel the last `events_subscribe` call handed to Rust. */
function channel(): FakeChannel {
  const subscribe = invokeMock.mock.calls.findLast(
    ([command]) => command === "events_subscribe",
  );
  return (subscribe?.[1] as { onEvent: FakeChannel }).onEvent;
}

const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

describe("event stream through Rust", () => {
  beforeEach(() => {
    invokeMock.mockReset();
    invokeMock.mockImplementation((command) =>
      Promise.resolve(command === "events_subscribe" ? 7 : null),
    );
  });

  it("subscribes with the project and since, and forwards events", async () => {
    const received: number[] = [];
    subscribeEvents({ project: "demo", since: 12 }, (event) =>
      received.push(event.seq),
    );
    await flush();
    expect(invokeMock).toHaveBeenCalledWith("events_subscribe", {
      project: "demo",
      since: 12,
      onEvent: channel(),
    });
    channel().onmessage({ kind: "event", event: envelope(13) });
    channel().onmessage({ kind: "event", event: envelope(14) });
    expect(received).toEqual([13, 14]);
  });

  it("never passes a token or a daemon URL to the webview's calls", async () => {
    subscribeEvents({ project: "demo" }, () => undefined);
    await flush();
    const args = JSON.stringify(invokeMock.mock.calls);
    expect(args).not.toMatch(/token|ws:\/\//);
  });

  it("reports a final stop and ignores events after unsubscribing", async () => {
    const onStop = vi.fn();
    const onEvent = vi.fn();
    const unsubscribe = subscribeEvents({ project: "demo", onStop }, onEvent);
    await flush();
    channel().onmessage({
      kind: "stopped",
      reason: "the daemon has no such project",
    });
    expect(onStop).toHaveBeenCalledWith("the daemon has no such project");

    unsubscribe();
    expect(invokeMock).toHaveBeenCalledWith("events_unsubscribe", { id: 7 });
    channel().onmessage({ kind: "event", event: envelope(1) });
    expect(onEvent).not.toHaveBeenCalled();
  });

  it("unsubscribes once Rust answers when stopped before that", async () => {
    const unsubscribe = subscribeEvents({ project: "demo" }, () => undefined);
    unsubscribe();
    await flush();
    expect(invokeMock).toHaveBeenCalledWith("events_unsubscribe", { id: 7 });
  });

  it("reports a refused subscription", async () => {
    invokeMock.mockImplementation(() =>
      // Tauri rejects with the serialised Rust error, a plain object.
      // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors
      Promise.reject({
        kind: "invalid_request",
        message: "not a project name",
      }),
    );
    const onStop = vi.fn();
    subscribeEvents({ project: "Bad", onStop }, () => undefined);
    await flush();
    expect(onStop).toHaveBeenCalledWith(
      expect.stringContaining("not a project name"),
    );
  });
});
