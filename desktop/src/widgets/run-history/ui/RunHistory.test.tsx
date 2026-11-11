import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api, DaemonError, type Schemas } from "@/shared/api";

import { RunHistory } from "./RunHistory";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return { ...actual, api: { GET: vi.fn() } };
});

type Handler = (path: string, init?: unknown) => unknown;
const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;
const ok = (data: unknown) =>
  Promise.resolve({ data, response: new Response() });

type Row = Schemas["RunRow"];
const row = (id: number, status: string, extra: Partial<Row> = {}): Row => ({
  id,
  kind: "ticket",
  ticket_id: `T${String(id).padStart(2, "0")}`,
  status,
  reason: null,
  started_at: "2026-11-07T14:00:00Z",
  ended_at: "2026-11-07T14:06:12Z",
  reset_at: null,
  progress_note: null,
  attempts: 1,
  last_attempt: 1,
  backend: "claude-code-cli",
  tokens: 182_000,
  cost_micro_usd: null,
  ...extra,
});

let pages: Record<string, { items: Row[]; next_cursor: string | null }>;
let fails: boolean;
const calls = {
  run: vi.fn<(runId: number, attempt: number | null) => void>(),
  ticket: vi.fn<(id: string) => void>(),
};

function show() {
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <RunHistory
        project="demo"
        empty={<p>No runs yet.</p>}
        onOpenRun={calls.run}
        onOpenTicket={calls.ticket}
      />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  fails = false;
  pages = { "": { items: [], next_cursor: null } };
  GET.mockImplementation((path, init) => {
    if (path === "/api/projects/{name}/tickets") {
      return ok({
        tickets: [{ id: "T01", meta: { title: "App shell" } }],
        invalid: [],
      });
    }
    if (path !== "/api/projects/{name}/runs") {
      throw new Error(`unexpected GET ${path}`);
    }
    if (fails) {
      return Promise.reject(
        new DaemonError({
          kind: "api",
          status: 500,
          code: "internal",
          message: "boom",
          field: null,
          etag: null,
          current: null,
        }),
      );
    }
    const query = (
      init as { params: { query: { cursor?: string; kind: string } } }
    ).params.query;
    expect(query).toMatchObject({ kind: "ticket", limit: 50 });
    return ok(pages[query.cursor ?? ""]);
  });
});

describe("Past runs", () => {
  it("renders each outcome as icon + label, with the row's columns", async () => {
    pages[""] = {
      items: [
        row(1, "done", { attempts: 3, tokens: 0, cost_micro_usd: 880_000 }),
        row(2, "blocked"),
        row(3, "awaiting_approval"),
        row(4, "cancelled", { attempts: 0, last_attempt: null, tokens: 0 }),
        row(5, "interrupted"),
        row(6, "paused", { ended_at: null }),
      ],
      next_cursor: null,
    };
    show();
    const table = await screen.findByRole("table");
    const rows = within(table).getAllByRole("row").slice(1);
    expect(rows).toHaveLength(6);
    for (const [index, label] of [
      "Merged",
      "Blocked",
      "Needs approval",
      "Cancelled",
      "Interrupted",
      "Paused",
    ].entries()) {
      const text = within(rows[index] as HTMLElement).getByText(label);
      expect(text.querySelector("svg")).not.toBeNull();
    }
    const first = within(rows[0] as HTMLElement);
    expect(first.getByText("App shell")).toBeInTheDocument();
    expect(first.getByText("3")).toBeInTheDocument();
    expect(first.getByText("6m 12s")).toBeInTheDocument();
    expect(first.getByText("$0.88")).toBeInTheDocument();
    expect(first.getByText(/ago$/)).toHaveAttribute(
      "title",
      new Date("2026-11-07T14:06:12Z").toLocaleString(),
    );
    expect(
      within(rows[1] as HTMLElement).getByText("182k tokens"),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Load more" })).toBeNull();
  });

  it("appends the next page on Load more", async () => {
    pages[""] = { items: [row(3, "done"), row(2, "done")], next_cursor: "c1" };
    pages.c1 = { items: [row(1, "blocked")], next_cursor: null };
    show();
    await userEvent.click(
      await screen.findByRole("button", { name: "Load more" }),
    );
    expect(await screen.findByText("Blocked")).toBeInTheDocument();
    expect(
      screen
        .getAllByRole("button", { name: /^Open T/ })
        .map((chip) => chip.textContent),
    ).toEqual(["T03", "T02", "T01"]);
    expect(screen.queryByRole("button", { name: "Load more" })).toBeNull();
  });

  it("opens the replay of the last attempt from a row, the drawer from a chip", async () => {
    pages[""] = {
      items: [row(1, "blocked", { attempts: 2, last_attempt: 5 })],
      next_cursor: null,
    };
    show();
    await userEvent.click(await screen.findByText("App shell"));
    expect(calls.run).toHaveBeenCalledWith(1, 5);
    await userEvent.click(
      screen.getByRole("button", { name: "Replay T01, run 1" }),
    );
    expect(calls.run).toHaveBeenCalledTimes(2);

    await userEvent.click(screen.getByRole("button", { name: "Open T01" }));
    expect(calls.ticket).toHaveBeenCalledWith("T01");
    expect(calls.run).toHaveBeenCalledTimes(2); // the chip doesn't open the replay
  });

  it("shows skeleton rows, then the empty state", async () => {
    show();
    expect(
      screen.getByRole("list", { name: "Loading past runs" }),
    ).toBeInTheDocument();
    expect(await screen.findByText("No runs yet.")).toBeInTheDocument();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("shows an error with Retry", async () => {
    fails = true;
    show();
    expect(
      await screen.findByText("Couldn't load the past runs: boom"),
    ).toBeInTheDocument();
    fails = false;
    pages[""] = { items: [row(1, "done")], next_cursor: null };
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("Merged")).toBeInTheDocument();
  });
});
