import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { subscribeEvents, type EventEnvelope } from "./events";

class MockSocket {
  static instances: MockSocket[] = [];
  readonly url: string;
  sent: string[] = [];
  closed: number | null = null;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: ((event: { code: number }) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    MockSocket.instances.push(this);
  }

  send(data: string): void {
    this.sent.push(data);
  }

  close(code: number): void {
    this.closed = code;
  }

  event(seq: number): void {
    const envelope = { seq, run_id: 1, attempt: null, ticket: "T01" };
    this.onmessage?.({
      data: JSON.stringify({ ...envelope, type: "log", ts: "", data: {} }),
    });
  }
}

const flush = () => vi.advanceTimersByTimeAsync(0);

function socket(index: number): MockSocket {
  const found = MockSocket.instances[index];
  if (found === undefined) {
    throw new Error(`no socket ${String(index)}`);
  }
  return found;
}

function start(onStop?: (reason: string) => void): EventEnvelope[] {
  const received: EventEnvelope[] = [];
  subscribeEvents(
    {
      port: 8765,
      project: "demo",
      getToken: () => Promise.resolve("secret-token"),
      WebSocketImpl: MockSocket as unknown as typeof WebSocket,
      ...(onStop ? { onStop } : {}),
    },
    (event) => received.push(event),
  );
  return received;
}

describe("event stream", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    MockSocket.instances = [];
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("authenticates first, then reconnects with since=<last seq> after 4408", async () => {
    const received = start();
    await flush();
    const first = socket(0);
    expect(first.url).toBe(
      "ws://127.0.0.1:8765/api/projects/demo/events?since=0",
    );
    first.onopen?.();
    expect(JSON.parse(first.sent[0] ?? "")).toEqual({
      type: "auth",
      token: "secret-token",
    });
    first.event(3);
    first.event(7);
    first.onmessage?.({ data: '{"type":"ping"}' });
    first.onclose?.({ code: 4408 });

    await vi.advanceTimersByTimeAsync(499);
    expect(MockSocket.instances).toHaveLength(1);
    await vi.advanceTimersByTimeAsync(1);
    const second = socket(1);
    expect(second.url).toBe(
      "ws://127.0.0.1:8765/api/projects/demo/events?since=7",
    );
    second.onopen?.();
    second.event(7); // already seen
    second.event(8);
    expect(received.map((event) => event.seq)).toEqual([3, 7, 8]);
  });

  it("backs off from 0.5 s to 10 s while the daemon is gone", async () => {
    start();
    await flush();
    const delays = [500, 1000, 2000, 4000, 8000, 10_000, 10_000];
    for (const [index, delay] of delays.entries()) {
      socket(index).onclose?.({ code: 1006 });
      await vi.advanceTimersByTimeAsync(delay - 1);
      expect(MockSocket.instances).toHaveLength(index + 1);
      await vi.advanceTimersByTimeAsync(1);
      expect(MockSocket.instances).toHaveLength(index + 2);
    }
  });

  it("stops on 4401 and when unsubscribed", async () => {
    const onStop = vi.fn();
    start(onStop);
    await flush();
    socket(0).onclose?.({ code: 4401 });
    await vi.advanceTimersByTimeAsync(20_000);
    expect(MockSocket.instances).toHaveLength(1);
    expect(onStop).toHaveBeenCalledWith("the daemon rejected the token");

    const unsubscribe = subscribeEvents(
      {
        port: 8765,
        project: "demo",
        getToken: () => Promise.resolve("t"),
        WebSocketImpl: MockSocket as unknown as typeof WebSocket,
      },
      () => undefined,
    );
    await flush();
    unsubscribe();
    expect(socket(1).closed).toBe(1000);
  });
});
