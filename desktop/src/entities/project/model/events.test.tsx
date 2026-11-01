import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { queryKeys, subscribeEvents, type EventEnvelope } from "@/shared/api";

import { COALESCE_MS, useProjectEvents, type EventSource } from "./events";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return { ...actual, subscribeEvents: vi.fn() };
});

const subscribe = vi.mocked(subscribeEvents);

function Probe({ projects }: { projects: EventSource[] }) {
  useProjectEvents(projects);
  return null;
}

function envelope(seq: number, type = "run.status"): EventEnvelope {
  return {
    seq,
    type,
    ts: "2026-11-01T12:00:00Z",
    run_id: 1,
    ticket: "T01",
    attempt: null,
    data: {},
  };
}

describe("useProjectEvents", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    subscribe.mockReset();
    subscribe.mockReturnValue(() => undefined);
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("subscribes after the REST answer's latest_seq, never from zero", () => {
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, "invalidateQueries");
    render(
      <QueryClientProvider client={client}>
        <Probe projects={[{ name: "fresh", latest_seq: 41 }]} />
      </QueryClientProvider>,
    );

    expect(subscribe).toHaveBeenCalledTimes(1);
    expect(subscribe.mock.calls[0]?.[0]).toMatchObject({
      project: "fresh",
      since: 41,
    });

    // Written between the REST call and the subscribe: the daemon replays it after 41.
    const onEvent = subscribe.mock.calls[0]?.[1];
    act(() => {
      onEvent?.(envelope(42));
      vi.advanceTimersByTime(COALESCE_MS);
    });
    expect(invalidate).toHaveBeenCalledWith({ queryKey: queryKeys.projects });
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: queryKeys.runs("fresh"),
    });
  });

  it("resumes after the last event seen when it remounts", () => {
    const client = new QueryClient();
    const view = render(
      <QueryClientProvider client={client}>
        <Probe projects={[{ name: "again", latest_seq: 5 }]} />
      </QueryClientProvider>,
    );
    act(() => {
      subscribe.mock.calls[0]?.[1](envelope(9, "log"));
    });
    view.unmount();
    render(
      <QueryClientProvider client={client}>
        <Probe projects={[{ name: "again", latest_seq: 7 }]} />
      </QueryClientProvider>,
    );
    expect(subscribe.mock.calls[1]?.[0]).toMatchObject({ since: 9 });
  });
});
