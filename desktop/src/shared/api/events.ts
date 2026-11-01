/**
 * A project's live run events, through Rust.
 *
 * The Rust command `events_subscribe` holds the daemon WebSocket: it sends the auth
 * message, forwards each envelope over a Tauri channel, and reconnects with
 * `since=<last seq>` after a drop or a `4408 too_slow` close (backoff 0.5 s doubling to
 * 10 s). So the token stays out of the webview and the CSP needs no `ws://`. A 4401
 * (bad token), 4404 (unknown project) or refused origin ends the stream with `onStop`.
 * No React here.
 */
import { Channel } from "@tauri-apps/api/core";

import { call } from "./client";
import type { Schemas } from "./http";

export type EventEnvelope = Schemas["EventEnvelope"];

export interface EventStreamOptions {
  project: string;
  /** Start after this seq (default 0: everything stored). */
  since?: number;
  /** Called when the stream stops for good. */
  onStop?: (reason: string) => void;
}

type StreamMessage =
  { kind: "event"; event: EventEnvelope } | { kind: "stopped"; reason: string };

/** Start receiving `onEvent` calls; returns the function that stops the stream. */
export function subscribeEvents(
  options: EventStreamOptions,
  onEvent: (event: EventEnvelope) => void,
): () => void {
  let stopped = false;
  let id: number | null = null;
  const unsubscribe = (streamId: number): void => {
    call("events_unsubscribe", { id: streamId }).catch(() => undefined);
  };

  const channel = new Channel<StreamMessage>();
  channel.onmessage = (message) => {
    if (stopped) {
      return;
    }
    if (message.kind === "event") {
      onEvent(message.event);
    } else {
      options.onStop?.(message.reason);
    }
  };

  call<number>("events_subscribe", {
    project: options.project,
    since: options.since ?? 0,
    onEvent: channel,
  }).then(
    (streamId) => {
      if (stopped) {
        unsubscribe(streamId); // stopped before Rust answered
      } else {
        id = streamId;
      }
    },
    (error: unknown) => {
      if (!stopped) {
        options.onStop?.(
          error instanceof Error ? error.message : String(error),
        );
      }
    },
  );

  return () => {
    stopped = true;
    if (id !== null) {
      unsubscribe(id);
    }
  };
}
