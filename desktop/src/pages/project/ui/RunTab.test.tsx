import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useProjectEvents } from "@/entities/project";
import { useCurrentRun, type CurrentRun } from "@/entities/run";
import {
  api,
  DaemonError,
  subscribeEvents,
  type EventEnvelope,
  type Schemas,
} from "@/shared/api";

import type { PanelState } from "../model/state";
import { RunTab } from "./RunTab";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return {
    ...actual,
    api: { GET: vi.fn(), POST: vi.fn() },
    subscribeEvents: vi.fn(),
  };
});

type Handler = (path: string, init?: unknown) => unknown;
const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;
const POST = vi.mocked(api.POST) as unknown as ReturnType<
  typeof vi.fn<Handler>
>;
const ok = (data: unknown) =>
  Promise.resolve({ data, response: new Response() });

type Run = Schemas["RunDetail"];
type Attempt = Schemas["AttemptView"];

const attempt = (number: number, status = "running"): Attempt => ({
  number,
  kind: number === 1 ? "initial" : "gate_retry",
  status,
  backend: "claude-code-cli",
  model: null,
  input_tokens: 40_000,
  output_tokens: 2_000,
  cost_micro_usd: null,
  started_at: "2026-11-07T14:00:00Z",
  ended_at: null,
});

function runOf(extra: Partial<Run> = {}): Run {
  return {
    id: 7,
    kind: "ticket",
    ticket_id: "T15",
    status: "running",
    reason: null,
    started_at: "2026-11-07T14:00:00Z",
    ended_at: null,
    reset_at: null,
    progress_note: null,
    attempts: [attempt(1)],
    ...extra,
  };
}

function currentOf(run: Run | null, active: boolean): CurrentRun {
  return {
    project: "demo",
    active,
    working: active,
    run,
    attempts: run?.attempts.length ?? 0,
    input_tokens: 0,
    output_tokens: 0,
    cost_micro_usd: null,
    phases: [],
    last_merged: null,
    latest_seq: stored.at(-1)?.seq ?? 0,
  };
}

let seq = 0;
function ev(
  type: string,
  data: Record<string, unknown> = {},
  attemptNumber: number | null = 1,
  runId = 7,
): EventEnvelope {
  seq += 1;
  return {
    seq,
    run_id: runId,
    attempt: attemptNumber,
    ticket: "T15",
    type,
    ts: new Date(Date.UTC(2026, 10, 7, 14, 0, seq)).toISOString(),
    data,
  };
}
const step = (name: string, state: string, n = 1) =>
  ev("step", { step: name, state, attempt: n }, name === "worktree" ? null : n);

let stored: EventEnvelope[];
let runs: Map<number, Run>;
let current: CurrentRun;
let ticketAttempts: (Attempt & { run_id: number })[];
let listeners: Set<(event: EventEnvelope) => void>;
let currentFails: boolean;

/** Sends events to every open stream; Query notifies its observers on a timer. */
async function emit(...events: EventEnvelope[]) {
  await act(async () => {
    for (const event of events) {
      for (const listener of [...listeners]) {
        listener(event);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 10));
  });
}

const RUNNING: PanelState = {
  kind: "running",
  ticket: "T15",
  step: null,
  attempt: 1,
  tab: "run",
};
const READY: PanelState = { kind: "ready", next: "T11", tab: "tickets" };

const calls = {
  open: vi.fn<(id: string) => void>(),
  tickets: vi.fn<() => void>(),
  current: vi.fn<() => void>(),
};

function Harness({
  state,
  attemptParam,
}: {
  state: PanelState;
  attemptParam: number | null;
}) {
  const run = useCurrentRun("demo");
  useProjectEvents([{ name: "demo", latest_seq: current.latest_seq }]);
  return (
    <RunTab
      project="demo"
      current={run}
      state={state}
      attempt={attemptParam}
      ticket={null}
      onOpenTicket={calls.open}
      onShowTickets={calls.tickets}
      onShowCurrent={calls.current}
    />
  );
}

function show(state: PanelState = RUNNING, attemptParam: number | null = null) {
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <Harness state={state} attemptParam={attemptParam} />
    </QueryClientProvider>,
  );
}

const eventLoads = () =>
  GET.mock.calls.filter(
    ([path]) => path === "/api/projects/{name}/runs/{run_id}/events",
  );
const stepState = (label: string) =>
  within(screen.getByRole("list", { name: "Steps" }))
    .getByText(label)
    .closest("li")
    ?.getAttribute("data-state");

beforeEach(() => {
  vi.clearAllMocks();
  seq = 0;
  stored = [];
  listeners = new Set();
  currentFails = false;
  runs = new Map([[7, runOf()]]);
  current = currentOf(runs.get(7) ?? null, true);
  ticketAttempts = [];
  vi.mocked(subscribeEvents).mockImplementation((_options, onEvent) => {
    listeners.add(onEvent);
    return () => {
      listeners.delete(onEvent);
    };
  });
  POST.mockImplementation(() => ok({}));
  GET.mockImplementation((path, init) => {
    const params = (
      init as {
        params?: {
          path?: { run_id?: number };
          query?: { attempt?: number; after?: number };
        };
      }
    ).params;
    switch (path) {
      case "/api/projects/{name}/runs/current":
        return currentFails
          ? Promise.reject(
              new DaemonError({
                kind: "api",
                status: 500,
                code: "internal",
                message: "boom",
                field: null,
                etag: null,
                current: null,
              }),
            )
          : ok(current);
      case "/api/projects/{name}/runs/{run_id}":
        return ok(runs.get(params?.path?.run_id ?? 0));
      case "/api/projects/{name}/runs/{run_id}/events": {
        const after = params?.query?.after ?? 0;
        const items = stored.filter(
          (e) => e.seq > after && e.run_id === params?.path?.run_id,
        );
        return ok({ items, next_after: null });
      }
      case "/api/projects/{name}/tickets":
        return ok({
          tickets: [{ id: "T15", meta: { title: "Demands page and dialogs" } }],
          invalid: [],
        });
      case "/api/projects/{name}/tickets/{ticket_id}":
        return ok({ attempts: ticketAttempts });
      case "/api/projects/{name}/settings":
        return ok({
          settings: { limits: { gate_retries: 3, review_retries: 0 } },
        });
      case "/api/agents":
        return ok({
          backends: [
            {
              name: "claude-code-cli",
              installed: true,
              logged_in: true,
              reason: null,
            },
          ],
          graphify: { installed: false, version: null, tested: false },
        });
      case "/api/settings":
        return ok({ secrets: { anthropic: { set: false, source: null } } });
    }
    throw new Error(`unexpected GET ${path}`);
  });
});

describe("Run tab, live", () => {
  it("plays a full fake run live, from the steps to Merged, with no reload", async () => {
    stored = [
      ev("run.started", { ticket_id: "T15" }, null),
      step("worktree", "running"),
      step("worktree", "passed"),
      ev("attempt.started", { number: 1, kind: "initial" }),
      step("implement", "running"),
    ];
    current = currentOf(runs.get(7) ?? null, true);
    show();

    expect(
      await screen.findByRole("button", { name: "Demands page and dialogs" }),
    ).toBeInTheDocument();
    expect(await screen.findByText("Attempt 1 of 4")).toBeInTheDocument();
    expect(screen.getByText("Claude Code")).toBeInTheDocument();
    await waitFor(() => {
      expect(stepState("Implement")).toBe("running");
    });
    expect(stepState("Worktree")).toBe("passed");

    await emit(
      ev("agent.message", { text: "Adding the **status filter**." }),
      ev("agent.tool_call", {
        id: "t1",
        name: "Bash",
        input_summary: '{"command": "just test --filter demands"}',
      }),
      ev("agent.tool_result", {
        id: "t1",
        text: "4 passed",
        lines: 1,
        is_error: false,
      }),
      ev("agent.file_edit", {
        path: "src/DemandsTable.tsx",
        added: 1,
        removed: 2,
      }),
      step("implement", "passed"),
      step("gates", "running"),
    );
    const log = screen.getByRole("log", { name: "Transcript" });
    const text = log.textContent;
    expect(text.indexOf("status filter")).toBeLessThan(
      text.indexOf("just test --filter demands"),
    );
    expect(text.indexOf("just test")).toBeLessThan(
      text.indexOf("src/DemandsTable.tsx"),
    );
    expect(within(log).getByText("1.0s")).toBeInTheDocument();
    expect(within(log).getByText("+1")).toBeInTheDocument();
    expect(within(log).getByText("−2")).toBeInTheDocument();
    expect(stepState("Gates")).toBe("running");

    await emit(
      step("gates", "passed"),
      step("review", "running"),
      step("review", "passed"),
      step("policy", "running"),
      step("policy", "passed"),
      step("integrate", "running"),
    );
    expect(stepState("Review")).toBe("passed");
    expect(stepState("Integrate")).toBe("running");

    runs.set(
      7,
      runOf({
        status: "done",
        ended_at: "2026-11-07T14:06:12Z",
        attempts: [attempt(1, "approved")],
      }),
    );
    current = currentOf(runs.get(7) ?? null, false);
    await emit(
      ev("integrate", { commit: "a1b2c3d4e5f6", tag: "ticket/T15" }, null),
      step("integrate", "passed"),
      ev("run.status", { from: "running", to: "done" }, null),
    );
    expect(await screen.findByText("Merged as a1b2c3d")).toBeInTheDocument();
    expect(screen.getByText("6m 12s")).toBeInTheDocument();
    expect(eventLoads()).toHaveLength(1);
  });

  it("opens mid-run with the earlier events, then live ones, with no gap or duplicate", async () => {
    stored = [
      ev("attempt.started", { number: 1, kind: "initial" }),
      step("implement", "running"),
      ev("agent.message", { text: "Earlier message" }),
    ];
    current = currentOf(runs.get(7) ?? null, true);
    show();

    expect(await screen.findByText("Earlier message")).toBeInTheDocument();
    const load = eventLoads()[0]?.[1] as { params: { query: unknown } };
    expect(load.params.query).toMatchObject({ attempt: 1, after: 0 });
    // The run's own stream starts after the last event loaded.
    expect(
      vi.mocked(subscribeEvents).mock.calls.some(([o]) => o.since === 3),
    ).toBe(true);

    const replayed = stored[2];
    if (replayed === undefined) {
      throw new Error("no event");
    }
    await emit(replayed, ev("agent.message", { text: "Live message" }));
    expect(await screen.findByText("Live message")).toBeInTheDocument();
    expect(screen.getAllByText("Earlier message")).toHaveLength(1);
  });

  it("shows a failed gates step in red, then moves to attempt 2 on the retry", async () => {
    stored = [
      ev("attempt.started", { number: 1, kind: "initial" }),
      step("implement", "passed"),
      step("gates", "running"),
    ];
    show();
    await waitFor(() => {
      expect(stepState("Gates")).toBe("running");
    });

    await emit(step("gates", "failed"));
    expect(stepState("Gates")).toBe("failed");
    const gates = within(screen.getByRole("list", { name: "Steps" }))
      .getByText("Gates")
      .closest("li");
    expect(gates).toHaveClass("text-danger");
    expect(gates).toHaveTextContent("Gates: failed");

    await emit(
      ev("attempt.started", { number: 2, kind: "gate_retry" }, 2),
      step("implement", "running", 2),
    );
    expect(await screen.findByText("Attempt 2 of 4")).toBeInTheDocument();
    expect(stepState("Implement")).toBe("running");
    expect(stepState("Gates")).toBe("pending");
  });

  it("shows a denied command in red and caps a long tool result at 200 lines", async () => {
    stored = [ev("attempt.started", { number: 1, kind: "initial" })];
    show();
    await screen.findByRole("log", { name: "Transcript" });
    const long = Array.from({ length: 200 }, (_, n) => `line ${String(n)}`);
    await emit(
      ev("agent.denied", {
        tool: "Bash",
        input_summary: '{"command": "rm -rf /"}',
        reason: "denied",
      }),
      ev("agent.tool_call", {
        id: "t2",
        name: "Read",
        input_summary: '{"file_path": "big.log"}',
      }),
      ev("agent.tool_result", {
        id: "t2",
        text: long.join("\n"),
        lines: 450,
        is_error: false,
      }),
    );
    const denied = screen.getByText("Denied by policy").parentElement;
    expect(denied).toHaveClass("text-danger");
    expect(denied).toHaveTextContent("Bash rm -rf /");

    expect(screen.queryByText(/Showing 200/)).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: /big\.log/ }));
    expect(screen.getByText("Showing 200 of 450 lines")).toBeInTheDocument();
    expect(screen.getByText(/line 199/)).toBeInTheDocument();
  });

  it("renders <script>, an image and a javascript: link in an agent message inert", async () => {
    stored = [
      ev("attempt.started", { number: 1, kind: "initial" }),
      ev("agent.message", {
        text: '<script>alert(1)</script>\n\n<img src="x" onerror="alert(1)">\n\n[run me](javascript:alert(1))',
      }),
    ];
    show();
    const link = await screen.findByText("run me");
    const log = screen.getByRole("log", { name: "Transcript" });
    expect(log.querySelector("script")).toBeNull();
    expect(log.querySelector("img")).toBeNull();
    expect(log.querySelector("[onerror]")).toBeNull();
    expect(link.closest("a")?.getAttribute("href") ?? "").not.toContain(
      "javascript",
    );
  });

  it("offers Jump to latest when scrolled up, and scrolls down on click", async () => {
    stored = [
      ev("attempt.started", { number: 1, kind: "initial" }),
      ev("agent.message", { text: "Hello" }),
    ];
    show();
    const log = await screen.findByRole("log", { name: "Transcript" });
    Object.defineProperty(log, "scrollHeight", {
      configurable: true,
      value: 1000,
    });
    Object.defineProperty(log, "clientHeight", {
      configurable: true,
      value: 200,
    });
    expect(screen.queryByRole("button", { name: "Jump to latest" })).toBeNull();

    log.scrollTop = 100;
    fireEvent.scroll(log);
    await userEvent.click(
      await screen.findByRole("button", { name: "Jump to latest" }),
    );
    expect(log.scrollTop).toBe(1000);
    expect(screen.queryByRole("button", { name: "Jump to latest" })).toBeNull();
  });

  it("offers View T16 when Run all started the next ticket", async () => {
    stored = [ev("attempt.started", { number: 1, kind: "initial" })];
    show();
    await screen.findByText("Attempt 1 of 4");

    runs.set(7, runOf({ status: "done", ended_at: "2026-11-07T14:06:00Z" }));
    runs.set(8, runOf({ id: 8, ticket_id: "T16" }));
    current = currentOf(runs.get(8) ?? null, true);
    await emit(
      ev("integrate", { commit: "a1b2c3d4", tag: "ticket/T15" }, null),
      ev("run.status", { from: "running", to: "done" }, null),
      ev("run.started", { ticket_id: "T16" }, null, 8),
    );
    expect(await screen.findByText("· Next: T16 started")).toBeInTheDocument();
    expect(screen.getByText("Merged as a1b2c3d")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "View T16" }));
    expect(
      await screen.findByRole("button", { name: "Open T16" }),
    ).toBeInTheDocument();
  });
});

describe("Run tab, no active run", () => {
  it("says no runs yet and leads to the Tickets tab", async () => {
    current = currentOf(null, false);
    show(READY);
    expect(await screen.findByText("No runs yet.")).toBeInTheDocument();
    expect(
      screen.getByText("Approve the plan, then press Run next."),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Open Tickets" }));
    expect(calls.tickets).toHaveBeenCalled();
  });

  it("summarises the last run and offers Run next", async () => {
    current = currentOf(
      runOf({
        ticket_id: "T09",
        status: "blocked",
        ended_at: new Date().toISOString(),
      }),
      false,
    );
    show(READY);
    const last = await screen.findByRole("region", { name: "Last run" });
    expect(within(last).getByText("T09")).toBeInTheDocument();
    expect(within(last).getByText("Blocked")).toBeInTheDocument();
    expect(within(last).getByText("just now")).toBeInTheDocument();
    await userEvent.click(
      within(last).getByRole("button", { name: "Run next (T11)" }),
    );
    expect(POST).toHaveBeenCalledWith(
      "/api/projects/{name}/run/next",
      expect.anything(),
    );
  });

  it("gives Run next's disabled reason", async () => {
    current = currentOf(runOf({ status: "done" }), false);
    show({ kind: "idle", reason: "All tickets done", tab: "tickets" });
    const last = await screen.findByRole("region", { name: "Last run" });
    expect(
      within(last).getByRole("button", { name: "Run next" }),
    ).toBeDisabled();
    expect(within(last).getByText("All tickets done")).toBeInTheDocument();
  });

  it("shows a finished ?attempt=N with Show current run", async () => {
    current = currentOf(runOf({ status: "blocked" }), false);
    ticketAttempts = [
      {
        ...attempt(2, "gates_failed"),
        ended_at: new Date().toISOString(),
        run_id: 7,
      },
    ];
    show(READY, 2);
    const shown = await screen.findByRole("region", { name: "Attempt 2" });
    expect(within(shown).getByText("Gates failed")).toBeInTheDocument();
    expect(
      screen.getByText("Full replay of the transcript comes in T40."),
    ).toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: "Show current run" }),
    );
    expect(calls.current).toHaveBeenCalled();
  });

  it("sends ?attempt=N of the running attempt to the live view", async () => {
    ticketAttempts = [{ ...attempt(1), run_id: 7 }];
    show(RUNNING, 1);
    await waitFor(() => {
      expect(calls.current).toHaveBeenCalled();
    });
  });

  it("shows loading, then an error with Retry", async () => {
    currentFails = true;
    show();
    expect(screen.getByText("Loading the run…")).toBeInTheDocument();
    expect(
      await screen.findByText("Couldn't load the run: boom"),
    ).toBeInTheDocument();
    currentFails = false;
    current = currentOf(null, false);
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("No runs yet.")).toBeInTheDocument();
  });
});
