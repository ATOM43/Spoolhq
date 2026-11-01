/**
 * A project's live run events over the daemon's WebSocket.
 *
 * Sends the auth message first (a browser can't set headers on a WebSocket), tracks the
 * last `seq` and, after a drop or a `4408 too_slow` close, reconnects with
 * `since=<last seq>` so nothing is missed or repeated (backoff 0.5 s doubling to 10 s).
 * A `4401` (bad token) or `4404` (unknown project) close stops it. No React here.
 */
import type { Schemas } from "./http";

export type EventEnvelope = Schemas["EventEnvelope"];

export interface EventStreamOptions {
  port: number;
  project: string;
  /** The daemon token; asked for on every (re)connect. */
  getToken: () => Promise<string>;
  /** Start after this seq (default 0: everything stored). */
  since?: number;
  /** Called when the stream stops for good: 4401, 4404 or a token error. */
  onStop?: (reason: string) => void;
  /** For tests. */
  WebSocketImpl?: typeof WebSocket;
}

const FINAL_CLOSES: Record<number, string> = {
  4401: "the daemon rejected the token",
  4404: "the daemon has no such project",
};
const FIRST_DELAY_MS = 500;
const MAX_DELAY_MS = 10_000;

/** Start receiving `onEvent` calls; returns the function that stops the stream. */
export function subscribeEvents(
  options: EventStreamOptions,
  onEvent: (event: EventEnvelope) => void,
): () => void {
  const Impl = options.WebSocketImpl ?? WebSocket;
  let lastSeq = options.since ?? 0;
  let delay = FIRST_DELAY_MS;
  let socket: WebSocket | null = null;
  let timer: ReturnType<typeof setTimeout> | null = null;
  let stopped = false;

  const stop = (reason?: string): void => {
    stopped = true;
    if (timer !== null) {
      clearTimeout(timer);
    }
    socket?.close(1000);
    if (reason !== undefined) {
      options.onStop?.(reason);
    }
  };

  const reconnect = (): void => {
    if (stopped) {
      return;
    }
    timer = setTimeout(() => {
      timer = null;
      void connect();
    }, delay);
    delay = Math.min(delay * 2, MAX_DELAY_MS);
  };

  const connect = async (): Promise<void> => {
    let token: string;
    try {
      token = await options.getToken();
    } catch (error) {
      stop(error instanceof Error ? error.message : String(error));
      return;
    }
    if (stopped) {
      return;
    }
    const project = encodeURIComponent(options.project);
    const url = `ws://127.0.0.1:${String(options.port)}/api/projects/${project}/events?since=${String(lastSeq)}`;
    const ws = new Impl(url);
    socket = ws;
    ws.onopen = () => {
      ws.send(JSON.stringify({ type: "auth", token }));
      delay = FIRST_DELAY_MS;
    };
    ws.onmessage = (message: MessageEvent) => {
      const data: unknown = JSON.parse(String(message.data));
      if (!isEnvelope(data) || data.seq <= lastSeq) {
        return; // a ping, or something already seen
      }
      lastSeq = data.seq;
      onEvent(data);
    };
    ws.onclose = (event: CloseEvent) => {
      if (socket !== ws || stopped) {
        return;
      }
      socket = null;
      const final = FINAL_CLOSES[event.code];
      if (final !== undefined) {
        stop(final);
        return;
      }
      reconnect();
    };
  };

  void connect();
  return () => {
    stop();
  };
}

function isEnvelope(value: unknown): value is EventEnvelope {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as { seq?: unknown }).seq === "number"
  );
}
