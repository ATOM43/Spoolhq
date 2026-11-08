import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  api,
  DaemonError,
  subscribeEvents,
  type EventEnvelope,
  type Schemas,
} from "@/shared/api";

import { FinishedAttempt } from "./NoRun";
import { RunView } from "./RunView";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return { ...actual, api: { GET: vi.fn() }, subscribeEvents: vi.fn() };
});

type Handler = (path: string, init?: unknown) => unknown;
const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;
const ok = (data: unknown) =>
  Promise.resolve({ data, response: new Response() });
const apiError = (status: number, code: string) =>
  Promise.reject(
    new DaemonError({
      kind: "api",
      status,
      code,
      message: code,
      field: null,
      etag: null,
      current: null,
    }),
  );

const XSS = "<script>alert(1)</script> [x](javascript:alert(1))";

const GATES: Schemas["GatesReport"] = {
  passed: false,
  stopped: null,
  results: [
    {
      name: "install",
      command: "just install",
      state: "passed",
      duration_ms: 12_000,
      output: "",
      first_failure_line: null,
      truncated: false,
    },
    {
      name: "lint",
      command: "just lint",
      state: "passed",
      duration_ms: 4_000,
      output: XSS,
      first_failure_line: null,
      truncated: false,
    },
    {
      name: "test",
      command: "just test",
      state: "failed",
      duration_ms: 41_000,
      output: `collected 3 items\n${XSS}\nFAILED tests/test_a.py::test_b\n1 failed`,
      first_failure_line: 2,
      truncated: true,
    },
  ],
};

const REVIEW = (
  verdict: Schemas["ReviewReport"]["verdict"],
): Schemas["ReviewReport"] => ({
  verdict,
  summary: "One item is missing.",
  stopped: null,
  items: [
    { text: "Migrations run", met: true, reason: "`just test` passed" },
    { text: "Rollback works", met: false, reason: XSS },
  ],
});

const DIFF: Schemas["DiffReport"] = {
  truncated: true,
  files: [
    {
      path: "src/app.py",
      old_path: null,
      status: "modified",
      additions: 2,
      deletions: 1,
      binary: false,
      truncated: false,
      patch: `@@ -1,2 +1,3 @@\n keep\n-${XSS}\n+new one\n+new two`,
    },
    {
      path: "src/new_name.py",
      old_path: "src/old_name.py",
      status: "renamed",
      additions: 0,
      deletions: 0,
      binary: false,
      truncated: false,
      patch: "",
    },
    {
      path: "logo.png",
      old_path: null,
      status: "added",
      additions: 0,
      deletions: 0,
      binary: true,
      truncated: false,
      patch: "",
    },
    {
      path: "big.py",
      old_path: null,
      status: "added",
      additions: 2000,
      deletions: 0,
      binary: false,
      truncated: true,
      patch: [
        "@@ -0,0 +1,2000 @@",
        ...Array.from({ length: 80 }, (_, i) => `+line ${String(i)}`),
      ].join("\n"),
    },
  ],
};

let reports: Partial<Record<"gates" | "review" | "diff", unknown>>;
let stored: EventEnvelope[];
let listeners: Set<(event: EventEnvelope) => void>;
let seq: number;

function ev(type: string, data: Record<string, unknown>): EventEnvelope {
  seq += 1;
  return {
    seq,
    run_id: 7,
    attempt: 1,
    ticket: "T15",
    type,
    ts: new Date(Date.UTC(2026, 10, 7, 14, 0, seq)).toISOString(),
    data,
  };
}
const step = (name: string, state: string, extra = {}) =>
  ev("step", { step: name, state, attempt: 1, ...extra });

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

const RUN = {
  id: 7,
  kind: "ticket",
  ticket_id: "T15",
  status: "running",
  reason: null,
  started_at: "2026-11-07T14:00:00Z",
  ended_at: null,
  reset_at: null,
  progress_note: null,
  attempts: [
    {
      number: 1,
      kind: "initial",
      status: "running",
      backend: null,
      model: null,
      input_tokens: 0,
      output_tokens: 0,
      cost_micro_usd: null,
      started_at: "2026-11-07T14:00:00Z",
      ended_at: null,
    },
  ],
};

function wrap(ui: React.ReactNode) {
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      {ui}
    </QueryClientProvider>,
  );
}

async function showLive() {
  wrap(
    <RunView
      project="demo"
      runId={7}
      since={0}
      next={null}
      onViewNext={() => undefined}
      onOpenTicket={() => undefined}
      runNext={null}
    />,
  );
  await screen.findByRole("region", { name: "Details" });
}

const details = () => screen.getByRole("region", { name: "Details" });
const tab = (name: RegExp) =>
  userEvent.click(within(details()).getByRole("tab", { name }));
const artifactCalls = (name: string) =>
  GET.mock.calls.filter(([path]) => path.endsWith(`/${name}`)).length;

beforeEach(() => {
  vi.clearAllMocks();
  seq = 0;
  reports = {};
  listeners = new Set();
  stored = [];
  vi.mocked(subscribeEvents).mockImplementation((_options, onEvent) => {
    listeners.add(onEvent);
    return () => {
      listeners.delete(onEvent);
    };
  });
  GET.mockImplementation((path) => {
    const artifact = /attempts\/\{number\}\/(gates|review|diff)$/.exec(path);
    if (artifact) {
      const report = reports[artifact[1] as "gates" | "review" | "diff"];
      return report === undefined ? apiError(404, "not_ready") : ok(report);
    }
    switch (path) {
      case "/api/projects/{name}/runs/{run_id}":
        return ok(RUN);
      case "/api/projects/{name}/runs/{run_id}/events":
        return ok({ items: stored, next_after: null });
      case "/api/projects/{name}/tickets":
        return ok({ tickets: [], invalid: [] });
      case "/api/projects/{name}/settings":
        return ok({ settings: { limits: {} } });
      case "/api/projects/{name}/tickets/{ticket_id}":
        return ok({
          attempts: [{ ...RUN.attempts[0], status: "gates_failed", run_id: 7 }],
        });
    }
    throw new Error(`unexpected GET ${path}`);
  });
});

describe("Gates panel", () => {
  it("goes from before, to running with the rows so far, to the failed gate open at its line", async () => {
    stored = [step("implement", "running")];
    await showLive();
    expect(
      await within(details()).findByText("Gates run after the agent finishes."),
    ).toBeInTheDocument();

    await emit(
      step("implement", "passed"),
      step("gates", "running", {
        gate: "test",
        command: "just test",
        done: [
          {
            name: "install",
            command: "just install",
            status: "passed",
            duration_ms: 12_000,
          },
          {
            name: "lint",
            command: "just lint",
            status: "passed",
            duration_ms: 4_000,
          },
        ],
      }),
    );
    const list = within(details()).getByRole("list", { name: "Gates" });
    expect(within(list).getAllByText("Passed")).toHaveLength(2);
    expect(within(list).getByText(/^Running/)).toHaveTextContent(
      "Running just test…",
    );
    const before = artifactCalls("gates");

    reports.gates = GATES;
    await emit(step("gates", "failed"));
    await waitFor(() => {
      expect(within(details()).getByText("Failed")).toBeInTheDocument();
    });
    expect(artifactCalls("gates")).toBe(before + 1); // refetched once, on the step's end
    const failed = within(details()).getByRole("button", { name: /just test/ });
    expect(failed).toHaveAttribute("aria-expanded", "true");
    expect(failed).toHaveTextContent("41s");
    const mark = details().querySelector("[data-failure]");
    expect(mark).toHaveTextContent("FAILED tests/test_a.py::test_b");
    expect(mark).toHaveTextContent("First failure:");
    expect(within(details()).getByText(/Output trimmed/)).toBeInTheDocument();
    // Passed rows with output are closed; a click opens them.
    const lint = within(details()).getByRole("button", { name: /just lint/ });
    expect(lint).toHaveAttribute("aria-expanded", "false");
    await userEvent.click(lint);
    expect(lint).toHaveAttribute("aria-expanded", "true");
    // Untrusted output stays text.
    expect(details().querySelector("script, a")).toBeNull();
    expect(within(details()).getAllByText(XSS).length).toBeGreaterThan(0);
  });

  it("says when the implementer stopped and shows load errors with Retry", async () => {
    reports.gates = { passed: false, results: [], stopped: "max_turns" };
    stored = [step("gates", "failed")];
    await showLive();
    expect(
      await within(details()).findByText(/stopped early \(max turns\)/),
    ).toBeInTheDocument();
  });

  it("shows an error with Retry", async () => {
    stored = [step("gates", "failed")];
    const base = GET.getMockImplementation();
    GET.mockImplementation((path, init) =>
      path.endsWith("/gates") ? apiError(500, "internal") : base?.(path, init),
    );
    await showLive();
    expect(
      await within(details()).findByText(/Couldn't load the gates/),
    ).toBeInTheDocument();
    GET.mockImplementation(base ?? (() => undefined));
    reports.gates = GATES;
    await userEvent.click(
      within(details()).getByRole("button", { name: "Retry" }),
    );
    expect(await within(details()).findByText("Failed")).toBeInTheDocument();
  });
});

describe("Review panel", () => {
  it("says before and while reviewing, then each verdict and item", async () => {
    stored = [step("gates", "passed")];
    await showLive();
    await tab(/Review/);
    expect(
      await within(details()).findByText(
        "The reviewer checks the diff after the gates pass.",
      ),
    ).toBeInTheDocument();
    await emit(step("review", "running"));
    expect(within(details()).getByText("Reviewing…")).toBeInTheDocument();

    reports.review = REVIEW("changes_requested");
    await emit(step("review", "failed"));
    expect(
      await within(details()).findByText("Changes requested"),
    ).toBeInTheDocument();
    expect(within(details()).getByText("· 1 of 2 met")).toBeInTheDocument();
    const items = within(
      within(details()).getByRole("list", { name: "Done when" }),
    ).getAllByRole("listitem");
    expect(items[0]).toHaveTextContent("Met: Migrations run");
    expect(items[1]).toHaveTextContent("Not met: Rollback works");
    expect(details().querySelector("script")).toBeNull();
    expect(details().querySelector('a[href^="javascript"]')).toBeNull();
  });

  it.each([
    ["approve", "Approved"],
    ["needs_human", "Needs a person"],
  ] as const)("shows %s as icon and label", async (verdict, label) => {
    reports.review = REVIEW(verdict);
    stored = [step("review", "passed")];
    await showLive();
    await tab(/Review/);
    expect(await within(details()).findByText(label)).toBeInTheDocument();
  });
});

describe("Diff panel", () => {
  it("lists the files with totals and shows the selected file's diff", async () => {
    stored = [step("implement", "running")];
    await showLive();
    await tab(/Diff/);
    expect(
      await within(details()).findByText(
        "The diff appears once the agent has changed files.",
      ),
    ).toBeInTheDocument();

    reports.diff = DIFF;
    await emit(ev("run.phase", { phase: "commit", text: "commit" }));
    await within(details()).findByRole("list", { name: "Changed files" });
    expect(within(details()).getAllByText("4 files")).toHaveLength(2); // tab and totals
    const files = within(details()).getByRole("list", {
      name: "Changed files",
    });
    expect(
      within(files).getByText("src/old_name.py → src/new_name.py"),
    ).toBeInTheDocument();
    const view = within(details()).getByRole("region", {
      name: "Diff of src/app.py",
    });
    const lines = view.querySelectorAll("[data-kind]");
    expect([...lines].map((l) => l.getAttribute("data-kind"))).toEqual([
      "hunk",
      "context",
      "del",
      "add",
      "add",
    ]);
    expect(lines[3]).toHaveTextContent(/^2\+new one$/); // no old number, new line 2
    expect(lines[2]).toHaveTextContent(/^2−/); // old line 2, removed
    expect(view.querySelector("script, a")).toBeNull();

    await userEvent.click(within(files).getByRole("button", { name: /logo/ }));
    expect(
      within(details()).getByText("Binary file, not shown."),
    ).toBeInTheDocument();
    await userEvent.click(within(files).getByRole("button", { name: /big/ }));
    expect(
      within(details()).getByText("Diff cut at 2,000 lines."),
    ).toBeInTheDocument();
  });
});

describe("Transcript mini diff", () => {
  it("expands a file edit to its lines and opens it in the Diff tab", async () => {
    reports.diff = DIFF;
    stored = [
      ev("agent.file_edit", { path: "big.py", added: 80, removed: 0 }),
      ev("run.phase", { phase: "commit", text: "commit" }),
    ];
    await showLive();
    const log = await screen.findByRole("log", { name: "Transcript" });
    const row = within(log).getByRole("button", { name: /big\.py/ });
    expect(row).toHaveAttribute("aria-expanded", "false");
    await userEvent.click(row);
    expect(within(log).getByText("Showing 50 of 81 lines")).toBeInTheDocument();
    expect(log.querySelectorAll("[data-kind]")).toHaveLength(50);

    await userEvent.click(
      within(log).getByRole("button", { name: "Open in Diff" }),
    );
    expect(
      within(details()).getByRole("tab", { name: /Diff/ }),
    ).toHaveAttribute("aria-selected", "true");
    expect(
      within(details()).getByRole("button", { name: /big\.py/ }),
    ).toHaveAttribute("aria-pressed", "true");
  });
});

describe("A finished ?attempt=N", () => {
  it("shows that attempt's reports", async () => {
    reports.gates = GATES;
    wrap(
      <FinishedAttempt
        project="demo"
        ticket="T15"
        attempt={1}
        onOpenTicket={() => undefined}
        onShowCurrent={() => undefined}
      />,
    );
    expect(
      await within(
        await screen.findByRole("region", { name: "Details" }),
      ).findByText("Failed"),
    ).toBeInTheDocument();
    await tab(/Review/);
    expect(
      await within(details()).findByText("No review in this attempt."),
    ).toBeInTheDocument();
  });
});
