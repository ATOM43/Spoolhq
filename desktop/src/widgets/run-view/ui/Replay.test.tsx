import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  api,
  DaemonError,
  subscribeEvents,
  type EventEnvelope,
  type Schemas,
} from "@/shared/api";

import { Replay } from "./Replay";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return { ...actual, api: { GET: vi.fn() }, subscribeEvents: vi.fn() };
});

type Handler = (path: string, init?: unknown) => unknown;
const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;
const ok = (data: unknown) =>
  Promise.resolve({ data, response: new Response() });

const at = (minute: number) => new Date(2026, 10, 7, 14, minute).toISOString();
const attempt = (number: number, status: string): Schemas["AttemptView"] => ({
  number,
  kind: number === 1 ? "initial" : "gate_retry",
  status,
  backend: "claude-code-cli",
  model: null,
  input_tokens: 40_000,
  output_tokens: 2_000,
  cost_micro_usd: null,
  started_at: at(number - 1),
  ended_at: at(number),
});
const RUN: Schemas["RunDetail"] = {
  id: 7,
  kind: "ticket",
  ticket_id: "T15",
  status: "blocked",
  reason: "gates failed 3 times",
  started_at: at(0),
  ended_at: at(3),
  reset_at: null,
  progress_note: null,
  attempts: [
    attempt(1, "gates_failed"),
    attempt(2, "gates_failed"),
    attempt(3, "gates_failed"),
  ],
};

const event = (seq: number, number: number): EventEnvelope => ({
  seq,
  run_id: 7,
  attempt: number,
  ticket: "T15",
  type: "agent.message",
  ts: at(number),
  data: { text: `message ${String(seq)} of attempt ${String(number)}` },
});

/** Each events page, held until the test lets it go. */
let pages: (() => void)[];
let total: number;
const calls = {
  attempt: vi.fn<(attempt: number) => void>(),
  current: vi.fn<() => void>(),
  past: vi.fn<() => void>(),
};

function show(number: number | null, active = false) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const ui = (n: number | null) => (
    <QueryClientProvider client={client}>
      <Replay
        project="demo"
        runId={7}
        attempt={n}
        active={active}
        onAttempt={calls.attempt}
        onShowCurrent={calls.current}
        onShowPast={calls.past}
        onOpenTicket={() => undefined}
      />
    </QueryClientProvider>
  );
  const view = render(ui(number));
  return (n: number) => {
    view.rerender(ui(n));
  };
}

const banner = () => screen.findByRole("region", { name: "Replay" });
const eventCalls = () =>
  GET.mock.calls.filter(([path]) => path.endsWith("/events"));
const release = async () => {
  await vi.waitFor(() => {
    expect(pages.length).toBeGreaterThan(0);
  });
  pages.shift()?.();
};

beforeEach(() => {
  vi.clearAllMocks();
  pages = [];
  total = 1;
  GET.mockImplementation((path, init) => {
    const params = (
      init as {
        params: {
          path: { number?: number };
          query?: { attempt?: number; after?: number };
        };
      }
    ).params;
    const artifact = /attempts\/\{number\}\/(gates|review|diff)$/.exec(path);
    if (artifact) {
      const n = String(params.path.number);
      switch (artifact[1]) {
        case "gates":
          return ok({
            passed: false,
            stopped: null,
            results: [
              {
                name: "test",
                command: `just test-${n}`,
                state: "failed",
                duration_ms: 1000,
                output: "",
                first_failure_line: null,
                truncated: false,
              },
            ],
          });
        case "review":
          return ok({
            verdict: "changes_requested",
            summary: `review of attempt ${n}`,
            stopped: null,
            items: [],
          });
        default:
          return ok({
            truncated: false,
            files: [
              {
                path: `src/attempt_${n}.py`,
                old_path: null,
                status: "added",
                additions: 1,
                deletions: 0,
                binary: false,
                truncated: false,
                patch: "@@ -0,0 +1 @@\n+x",
              },
            ],
          });
      }
    }
    switch (path) {
      case "/api/projects/{name}/runs/{run_id}":
        return ok(RUN);
      case "/api/projects/{name}/runs/{run_id}/events": {
        const number = params.query?.attempt ?? 0;
        const after = params.query?.after ?? 0;
        const last = after + 1 === total;
        return new Promise((resolve) => {
          pages.push(() => {
            resolve({
              data: {
                items: [event(after + 1, number)],
                next_after: last ? null : after + 1,
                total,
              },
              response: new Response(),
            });
          });
        });
      }
      case "/api/projects/{name}/tickets":
        return ok({
          tickets: [{ id: "T15", meta: { title: "Demands page" } }],
          invalid: [],
        });
      case "/api/projects/{name}/settings":
        return ok({ settings: { limits: {} } });
    }
    throw new Error(`unexpected GET ${path}`);
  });
});

describe("Replay", () => {
  it("shows the banner, the attempt arrows and the way back", async () => {
    show(2);
    const region = within(await banner());
    expect(
      region.getByText(/^Viewing attempt 2 of 3 · finished \d\d:02/),
    ).toBeVisible();
    expect(region.getByText("Gates failed")).toBeVisible(); // its own verdict
    await userEvent.click(
      region.getByRole("button", { name: "Previous attempt" }),
    );
    expect(calls.attempt).toHaveBeenCalledWith(1);
    await userEvent.click(region.getByRole("button", { name: "Next attempt" }));
    expect(calls.attempt).toHaveBeenLastCalledWith(3);
    await userEvent.click(
      region.getByRole("button", { name: "Back to past runs" }),
    );
    expect(calls.past).toHaveBeenCalled();
    expect(
      region.queryByRole("button", { name: "Show current run" }),
    ).toBeNull();
  });

  it("opens the last attempt with the run's outcome and no Next", async () => {
    show(null, true);
    const region = within(await banner());
    expect(region.getByText(/^Viewing attempt 3 of 3/)).toBeVisible();
    expect(region.getByText("Blocked")).toBeVisible();
    expect(region.queryByRole("button", { name: "Next attempt" })).toBeNull();
    await userEvent.click(
      region.getByRole("button", { name: "Show current run" }),
    );
    expect(calls.current).toHaveBeenCalled();
    expect(
      region.queryByRole("button", { name: "Back to past runs" }),
    ).toBeNull();
  });

  it("says so when the run has no such attempt", async () => {
    show(9);
    expect(
      within(await banner()).getByText("T15's run has no attempt 9"),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Back to past runs" }),
    ).toBeInTheDocument();
  });

  it("pages the events in, counting, and never opens a live stream", async () => {
    total = 3;
    show(2);
    expect(await screen.findByText("Loading events…")).toBeInTheDocument();
    await release();
    expect(await screen.findByText("Loading events… 1 of 3")).toBeVisible();
    expect(screen.getByRole("progressbar")).toHaveAttribute("value", "1");
    await release();
    expect(await screen.findByText("Loading events… 2 of 3")).toBeVisible();
    await release();
    expect(
      await screen.findByText("message 3 of attempt 2"),
    ).toBeInTheDocument();
    expect(screen.getByText("message 1 of attempt 2")).toBeInTheDocument();
    expect(
      eventCalls().map(
        ([, init]) => (init as { params: { query: unknown } }).params.query,
      ),
    ).toEqual([
      { attempt: 2, after: 0, limit: 2000 },
      { attempt: 2, after: 1, limit: 2000 },
      { attempt: 2, after: 2, limit: 2000 },
    ]);
    expect(subscribeEvents).not.toHaveBeenCalled();
  });

  it("shows the attempt's own gates, review and diff, and no run control", async () => {
    const go = show(2);
    await release();
    const details = within(
      await screen.findByRole("region", { name: "Details" }),
    );
    expect(await details.findByText("just test-2")).toBeInTheDocument();
    await userEvent.click(details.getByRole("tab", { name: /Review/ }));
    expect(await details.findByText("review of attempt 2")).toBeInTheDocument();
    await userEvent.click(details.getByRole("tab", { name: /Diff/ }));
    expect(
      (await details.findAllByText("src/attempt_2.py")).length,
    ).toBeGreaterThan(0);
    // Final step states, and nothing that acts on a run.
    expect(screen.getByRole("list", { name: "Steps" })).toBeInTheDocument();
    for (const name of [
      /Run next/,
      /Run all/,
      "Pause",
      "Resume",
      "Cancel",
      "Unblock",
      "Review",
    ]) {
      expect(screen.queryByRole("button", { name })).toBeNull();
    }

    go(1); // another attempt: its own events and reports
    await release();
    expect(
      await screen.findByText("message 1 of attempt 1"),
    ).toBeInTheDocument();
    expect(
      await within(screen.getByRole("region", { name: "Details" })).findByText(
        "just test-1",
      ),
    ).toBeInTheDocument();

    go(2); // back: served from the cache, no new request
    expect(
      await screen.findByText("message 1 of attempt 2"),
    ).toBeInTheDocument();
    expect(eventCalls()).toHaveLength(2);
    expect(subscribeEvents).not.toHaveBeenCalled();
  });

  it("shows an error with Retry and the way back", async () => {
    GET.mockImplementation(() =>
      Promise.reject(
        new DaemonError({
          kind: "api",
          status: 404,
          code: "not_found",
          message: "no run 7",
          field: null,
          etag: null,
          current: null,
        }),
      ),
    );
    show(1);
    expect(
      await screen.findByText("Couldn't load the run: no run 7"),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Back to past runs" }),
    ).toBeInTheDocument();
  });
});
