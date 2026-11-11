import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SET_UP_FIRST } from "@/features/settings";
import type { Ticket, TicketDetail } from "@/entities/ticket";
import { api, DaemonError } from "@/shared/api";

import { RUN_GOING } from "./PrimaryAction";
import { TicketDrawer } from "./TicketDrawer";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return { ...actual, api: { GET: vi.fn(), POST: vi.fn(), PUT: vi.fn() } };
});

type Init = {
  params: { path: Record<string, string>; header?: Record<string, string> };
  body?: unknown;
};
type Handler = (path: string, init: Init) => unknown;
const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;
const POST = vi.mocked(api.POST) as unknown as ReturnType<
  typeof vi.fn<Handler>
>;
const PUT = vi.mocked(api.PUT) as unknown as ReturnType<typeof vi.fn<Handler>>;
const ok = (data: unknown, etag = "") =>
  Promise.resolve({
    data,
    response: new Response(null, { headers: etag ? { ETag: etag } : {} }),
  });
const apiError = (status: number, message: string, more = {}) =>
  new DaemonError({
    kind: "api",
    status,
    code: "x",
    message,
    field: null,
    etag: null,
    current: null,
    ...more,
  });

const ticket = (
  id: string,
  status: Ticket["meta"]["status"],
  depends_on: string[] = [],
): Ticket => ({
  id,
  file_name: `${id}-x.md`,
  meta: {
    id,
    title: `Ticket ${id}`,
    phase: 1,
    depends_on,
    status,
    estimate_h: 2,
    review_required: false,
  },
  body: "## Scope\n\n- do it\n\n## Done when\n\n- [ ] works\n",
  activity: null,
});

const NO_GIT: TicketDetail["git"] = {
  branch: null,
  commits: null,
  diff_lines: null,
  commit: null,
  commit_url: null,
  tag: null,
  pr_number: null,
  pr_url: null,
  pr_state: null,
  pr_checked_at: null,
};
const SHA = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678";
const run = (status: string, extra = {}) => ({
  id: 7,
  kind: "ticket",
  ticket_id: "x",
  status,
  reason: null,
  started_at: "2026-11-06T10:00:00Z",
  ended_at: null,
  reset_at: null,
  progress_note: null,
  ...extra,
});
const attempt = {
  number: 3,
  run_id: 7,
  kind: "gate_retry",
  status: "gates_failed",
  backend: "claude-code-cli",
  model: null,
  input_tokens: 150_000,
  output_tokens: 32_000,
  cost_micro_usd: null,
  started_at: "2026-11-06T10:00:00Z",
  ended_at: "2026-11-06T10:22:05Z",
};
const RULES = [
  { rule: "diff_size", detail: "612 lines > 400" },
  { rule: "protected_paths", detail: "migrations/" },
];

/** The fake daemon's files and runs; tests change it and the drawer refetches. */
let state: {
  tickets: Ticket[];
  runs: Record<string, Partial<TicketDetail>>;
  etags: Record<string, string>;
  active: boolean;
  ready: boolean;
  /** Attempt reports by name; a missing one is 404 `not_ready`. */
  reports: Partial<Record<"gates" | "review", unknown>>;
};

const gate = (name: string, state: string) => ({
  name,
  command: `just ${name}`,
  state,
  duration_ms: 1000,
  output: "",
  first_failure_line: null,
  truncated: false,
});
const FAILED_GATES = {
  passed: false,
  stopped: null,
  results: [
    gate("install", "passed"),
    gate("lint", "passed"),
    gate("test", "failed"),
  ],
};

function reset() {
  state = {
    tickets: [
      ticket("T01", "done"),
      ticket("T02", "ready", ["T01"]),
      ticket("T03", "ready", ["T02", "T04"]),
      ticket("T04", "blocked"),
      ticket("T05", "running"),
      ticket("T06", "awaiting_approval"),
      ticket("T07", "awaiting_approval"),
      ticket("T08", "draft"),
      ticket("T09", "done"),
    ],
    runs: {
      T01: { git: { ...NO_GIT, commit: SHA, tag: "ticket/T01" } },
      T04: {
        run: run("blocked", { reason: "gates failed after 2 retries" }),
        attempts: [attempt],
        git: { ...NO_GIT, branch: "feat/T04-x", commits: 2, diff_lines: 40 },
        review_retries_left: 1,
      },
      T06: {
        run: run("awaiting_approval", {
          policy: { mode: "approval", rules: RULES, summary: "" },
        }),
        attempts: [{ ...attempt, status: "approved" }],
        git: { ...NO_GIT, branch: "feat/T06-x", commits: 4, diff_lines: 612 },
      },
      T07: {
        run: run("awaiting_approval", {
          pr_number: 42,
          pr_url: "https://github.com/acme/demo/pull/42",
        }),
        git: {
          ...NO_GIT,
          pr_number: 42,
          pr_url: "https://github.com/acme/demo/pull/42",
          pr_state: "open",
          pr_checked_at: new Date().toISOString(),
        },
      },
      T09: {
        git: {
          ...NO_GIT,
          commit: SHA,
          commit_url: `https://github.com/acme/demo/commit/${SHA}`,
        },
      },
    },
    etags: {},
    active: false,
    ready: true,
    reports: { gates: FAILED_GATES },
  };
}

const detailOf = (id: string) => {
  const found = state.tickets.find((t) => t.id === id);
  return found
    ? { ...found, run: null, attempts: [], git: NO_GIT, ...state.runs[id] }
    : null;
};

beforeEach(() => {
  vi.clearAllMocks();
  reset();
  GET.mockImplementation((path, init) => {
    switch (path) {
      case "/api/projects/{name}":
        return ok({ name: "demo", default_branch: "main", remote: null });
      case "/api/projects/{name}/runs/current":
        return ok({ active: state.active, run: null, phases: [] });
      case "/api/projects/{name}/tickets":
        return ok({ tickets: state.tickets, invalid: [] });
      case "/api/projects/{name}/tickets/{ticket_id}": {
        const id = init.params.path.ticket_id ?? "";
        return ok(detailOf(id), state.etags[id] ?? `"${id}-1"`);
      }
      case "/api/projects/{name}/runs/{run_id}":
        return ok({ attempts: [] });
      case "/api/projects/{name}/runs/{run_id}/attempts/{number}/gates":
      case "/api/projects/{name}/runs/{run_id}/attempts/{number}/review": {
        const report =
          state.reports[path.endsWith("gates") ? "gates" : "review"];
        return report === undefined
          ? Promise.reject(apiError(404, "not ready", { code: "not_ready" }))
          : ok(report);
      }
      case "/api/projects/{name}/settings":
        return ok({
          settings: { limits: { gate_retries: 3, review_retries: 2 } },
        });
      case "/api/agents":
        return ok({
          backends: state.ready ? [{ installed: true, logged_in: true }] : [],
        });
      case "/api/settings":
        return ok({ secrets: {} });
    }
    throw new Error(`unexpected GET ${path}`);
  });
  POST.mockImplementation(() => ok({}));
  PUT.mockImplementation((_path, init) => {
    const id = init.params.path.ticket_id ?? "";
    const etag = state.etags[id] ?? `"${id}-1"`;
    if (init.params.header?.["if-match"] !== etag) {
      return Promise.reject(
        apiError(412, "changed on disk", { code: "edit_conflict", etag }),
      );
    }
    const { meta, body } = init.body as Ticket;
    state.tickets = state.tickets.map((t) =>
      t.id === id ? { ...t, meta, body } : t,
    );
    state.etags[id] = `"${id}-${String(Date.now())}"`;
    return ok({});
  });
});

function show(id: string, onShowRun = vi.fn()) {
  const view = render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <TicketDrawer
        project="demo"
        ticketId={id}
        onOpen={vi.fn()}
        onClose={vi.fn()}
        onShowRun={onShowRun}
      />
    </QueryClientProvider>,
  );
  return { ...view, drawer: within(screen.getByRole("complementary")) };
}

const PRIMARY = [
  "Run this ticket",
  "Open run",
  "Unblock",
  "Approve and merge",
  /^Copy PR link/,
  /^Copy commit/,
];

describe("primary action by status", () => {
  it.each([
    ["T02", "Run this ticket"],
    ["T08", "Run this ticket"],
    ["T05", "Open run"],
    ["T04", "Unblock"],
    ["T06", "Approve and merge"],
    ["T07", "Copy PR link (#42)"],
    ["T01", "Copy commit a1b2c3d"],
    ["T09", "Copy commit link"],
  ])("%s shows only %s", async (id, action) => {
    const { drawer } = show(id);
    expect(await drawer.findByRole("button", { name: action })).toBeVisible();
    const header = within(drawer.getByRole("banner"));
    const others = PRIMARY.filter((name) => name !== action).flatMap((name) =>
      header.queryAllByRole("button", { name }),
    );
    expect(others.filter((b) => b.textContent !== action)).toEqual([]);
  });

  it("says what an unmet dependency waits for, with chips", async () => {
    const { drawer } = show("T03");
    const run = await drawer.findByRole("button", { name: "Run this ticket" });
    expect(run).toBeDisabled();
    expect(run).toHaveAccessibleDescription("Waits for T02, T04");
    const header = within(drawer.getByRole("banner"));
    expect(header.getByRole("button", { name: "Open T02" })).toBeVisible();
    expect(header.getByRole("button", { name: "Open T04" })).toBeVisible();
  });

  it("runs a ready ticket and switches to the Run tab", async () => {
    const onShowRun = vi.fn();
    const { drawer } = show("T02", onShowRun);
    const run = await drawer.findByRole("button", { name: "Run this ticket" });
    await vi.waitFor(() => {
      expect(run).toBeEnabled();
    });
    await userEvent.click(run);
    expect(POST).toHaveBeenCalledWith(
      "/api/projects/{name}/run/ticket/{ticket_id}",
      { params: { path: { name: "demo", ticket_id: "T02" } } },
    );
    expect(onShowRun).toHaveBeenCalledWith();
  });
});

describe("disabled actions say why", () => {
  it.each([
    ["a run is going", "T02", "Run this ticket", RUN_GOING],
    ["a run is going", "T04", "Unblock", RUN_GOING],
    ["a run is going", "T06", "Approve and merge", RUN_GOING],
    ["no agent", "T02", "Run this ticket", SET_UP_FIRST],
    ["no agent", "T06", "Request changes", SET_UP_FIRST],
    ["a draft", "T08", "Run this ticket", "Approve the plan first"],
  ])("%s: %s %s", async (why, id, name, reason) => {
    state.active = why === "a run is going";
    state.ready = why !== "no agent";
    const { drawer } = show(id);
    await vi.waitFor(() => {
      expect(drawer.getByRole("button", { name })).toHaveAccessibleDescription(
        reason,
      );
    });
    expect(drawer.getByRole("button", { name })).toBeDisabled();
    if (reason === SET_UP_FIRST) {
      expect(
        drawer.getByRole("button", { name: "Open Settings" }),
      ).toBeVisible();
    }
  });
});

describe("note to the agent", () => {
  it("unblocks with a required note, the reset on by default", async () => {
    const onShowRun = vi.fn();
    const { drawer } = show("T04", onShowRun);
    await userEvent.click(
      await drawer.findByRole("button", { name: "Unblock" }),
    );
    const dialog = within(screen.getByRole("dialog", { name: "Unblock T04" }));
    expect(
      dialog.getByText("Attempt 3: gates failed after 2 retries"),
    ).toBeVisible();
    const start = dialog.getByRole("button", { name: "Start new attempt" });
    expect(start).toBeDisabled();
    expect(start).toHaveAccessibleDescription(
      "Write a note for the agent first",
    );
    expect(
      dialog.getByRole("checkbox", { name: "Reset retry count" }),
    ).toBeChecked();
    expect(
      await dialog.findByText("Starts attempt 4 of 6 · 2 review retries left"),
    ).toBeVisible();
    await userEvent.click(
      dialog.getByRole("checkbox", { name: "Reset retry count" }),
    );
    expect(
      dialog.getByText("Starts attempt 4 of 6 · 1 review retry left"),
    ).toBeVisible();
    await userEvent.click(
      dialog.getByRole("checkbox", { name: "Reset retry count" }),
    );
    expect(
      dialog.getByRole("textbox", { name: "Note to the agent" }),
    ).toHaveAttribute("maxlength", "4000");

    await userEvent.type(dialog.getByRole("textbox"), "Use the slug helper");
    await userEvent.click(
      dialog.getByRole("button", { name: "Start new attempt" }),
    );
    expect(POST).toHaveBeenCalledWith(
      "/api/projects/{name}/tickets/{ticket_id}/unblock",
      {
        params: { path: { name: "demo", ticket_id: "T04" } },
        body: { note: "Use the slug helper", reset_retries: true },
      },
    );
    expect(onShowRun).toHaveBeenCalled();
  });

  it("requests changes with the note", async () => {
    const onShowRun = vi.fn();
    const { drawer } = show("T06", onShowRun);
    await userEvent.click(
      await drawer.findByRole("button", { name: "Request changes" }),
    );
    const dialog = within(
      screen.getByRole("dialog", { name: "Request changes on T06" }),
    );
    expect(
      dialog.getByText(
        "Held by the merge policy: Diff 612 lines > 400, Touches migrations/",
      ),
    ).toBeVisible();
    expect(dialog.queryByRole("checkbox")).toBeNull();
    await userEvent.type(dialog.getByRole("textbox"), "Split the table out");
    await userEvent.click(
      dialog.getByRole("button", { name: "Start new attempt" }),
    );
    expect(POST).toHaveBeenCalledWith(
      "/api/projects/{name}/tickets/{ticket_id}/reject",
      {
        params: { path: { name: "demo", ticket_id: "T06" } },
        body: { note: "Split the table out" },
      },
    );
    expect(onShowRun).toHaveBeenCalled();
  });
});

describe("approve and merge", () => {
  it("goes through the confirm and shows the merge", async () => {
    POST.mockImplementation(() => {
      state.tickets = state.tickets.map((t) =>
        t.id === "T06" ? { ...t, meta: { ...t.meta, status: "done" } } : t,
      );
      state.runs.T06 = { git: { ...NO_GIT, commit: SHA } };
      return ok({});
    });
    const { drawer } = show("T06");
    await userEvent.click(
      await drawer.findByRole("button", { name: "Approve and merge" }),
    );
    const confirm = within(
      screen.getByRole("dialog", { name: "Merge T06 into main?" }),
    );
    expect(
      confirm.getByText(
        "612 changed lines in 4 commits are squashed onto main.",
      ),
    ).toBeVisible();
    expect(confirm.getByText("Diff 612 lines > 400")).toBeVisible();
    expect(POST).not.toHaveBeenCalled();
    await userEvent.click(
      confirm.getByRole("button", { name: "Merge into main" }),
    );
    expect(POST).toHaveBeenCalledWith(
      "/api/projects/{name}/tickets/{ticket_id}/approve",
      { params: { path: { name: "demo", ticket_id: "T06" } } },
    );
    // Done now: the drawer shows the done ticket's action.
    expect(
      await drawer.findByRole("button", { name: "Copy commit a1b2c3d" }),
    ).toBeVisible();
  });

  it("shows the merge result while the ticket still waits", async () => {
    const { drawer } = show("T06");
    await userEvent.click(
      await drawer.findByRole("button", { name: "Approve and merge" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Merge into main" }),
    );
    expect(await drawer.findByText("Merging…")).toBeVisible();
  });

  it("shows the integration error", async () => {
    POST.mockImplementation(() =>
      Promise.reject(apiError(409, "main has uncommitted changes")),
    );
    const { drawer } = show("T06");
    await userEvent.click(
      await drawer.findByRole("button", { name: "Approve and merge" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Merge into main" }),
    );
    expect(await drawer.findByRole("alert")).toHaveTextContent(
      "Couldn't merge: main has uncommitted changes",
    );
  });
});

describe("sections", () => {
  it("shows why it needs you, attempts and git", async () => {
    const onShowRun = vi.fn();
    const { drawer } = show("T06", onShowRun);
    const rules = await drawer.findByRole("list", { name: "Rules that fired" });
    expect(
      within(rules)
        .getAllByRole("listitem")
        .map((li) => li.textContent),
    ).toEqual(["Diff 612 lines > 400", "Touches migrations/"]);
    const attempts = within(drawer.getByRole("region", { name: "Attempts" }));
    const row = attempts.getByRole("button", { name: /^Attempt 3: Approved/ });
    expect(row).toHaveTextContent("22m 05s");
    expect(row).toHaveTextContent("182k tokens");
    expect(row).toHaveTextContent("claude-code-cli");
    await userEvent.click(row);
    expect(onShowRun).toHaveBeenCalledWith({ runId: 7, attempt: 3 });
    const git = within(drawer.getByRole("region", { name: "Git" }));
    expect(git.getByText("feat/T06-x")).toBeVisible();
    expect(git.getByText("4 ahead of main · 612 changed lines")).toBeVisible();
  });

  it("shows the blocked reason with its attempt", async () => {
    const { drawer } = show("T04");
    expect(
      await drawer.findByText("Attempt 3: gates failed after 2 retries"),
    ).toBeVisible();
    expect(
      drawer.getByRole("button", { name: "Open attempt 3 in the Run tab" }),
    ).toBeVisible();
  });

  it("shows the PR state and when it was checked", async () => {
    const { drawer } = show("T07");
    const why = await drawer.findByText(/^PR #42 · open ·/);
    expect(why).toHaveTextContent("PR #42 · open · checked just now");
  });

  it.each([
    ["T09", "Copy commit link", `https://github.com/acme/demo/commit/${SHA}`],
    ["T01", "Copy commit a1b2c3d", SHA],
    ["T07", "Copy PR link (#42)", "https://github.com/acme/demo/pull/42"],
  ])("%s: %s copies it", async (id, name, text) => {
    const writeText = vi.fn(() => Promise.resolve());
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });
    const { drawer } = show(id);
    await userEvent.click(await drawer.findByRole("button", { name }));
    expect(writeText).toHaveBeenCalledWith(text);
    expect(await drawer.findByText("Copied")).toBeVisible();
  });
});

describe("editing", () => {
  const edit = async (id: string) => {
    const view = show(id);
    const button = await view.drawer.findByRole("button", { name: "Edit" });
    await vi.waitFor(() => {
      expect(view.drawer.getByRole("button", { name: "Edit" })).toBeEnabled();
    });
    await userEvent.click(button);
    return {
      ...view,
      form: within(
        await view.drawer.findByRole("form", { name: `Edit ${id}` }),
      ),
    };
  };

  it.each([
    ["T05", "Locked while the ticket is running"],
    ["T06", "Locked while the ticket is waiting for approval"],
    ["T01", "Done tickets can't be edited"],
  ])("%s is locked: %s", async (id, note) => {
    const { drawer } = show(id);
    await vi.waitFor(() => {
      expect(
        drawer.getByRole("button", { name: "Edit" }),
      ).toHaveAccessibleDescription(note);
    });
    expect(drawer.getByRole("button", { name: "Edit" })).toBeDisabled();
    if (id !== "T01") {
      expect(
        within(drawer.getByRole("banner")).getAllByText(note),
      ).not.toHaveLength(0);
    }
  });

  it("saves through PUT with If-Match, and the edit survives a reload", async () => {
    const { form, unmount } = await edit("T02");
    const title = form.getByRole("textbox", { name: "Title" });
    await userEvent.clear(title);
    await userEvent.type(title, "Parse slugs better");
    const estimate = form.getByRole("spinbutton", { name: "Estimate (h)" });
    await userEvent.clear(estimate);
    await userEvent.type(estimate, "3.5");
    await userEvent.click(form.getByRole("button", { name: "Save" }));

    const [, init] = PUT.mock.calls[0] ?? [];
    expect(init?.params.header).toEqual({ "if-match": '"T02-1"' });
    const sent = init?.body as Ticket;
    expect(sent.meta).toMatchObject({
      title: "Parse slugs better",
      estimate_h: 3.5,
    });
    expect(sent.body).toBe(ticket("T02", "ready").body); // body untouched: same bytes
    unmount();

    const { drawer } = show("T02");
    expect(
      await drawer.findByRole("heading", { name: "Parse slugs better" }),
    ).toBeVisible();
    expect(await drawer.findByText("3.5 h")).toBeVisible();
  });

  it("refuses an estimate off the half-hour steps", async () => {
    const { form } = await edit("T02");
    const estimate = form.getByRole("spinbutton", { name: "Estimate (h)" });
    await userEvent.clear(estimate);
    await userEvent.type(estimate, "9");
    expect(
      form.getByText("Between 0.5 and 8 h, in steps of 0.5"),
    ).toBeVisible();
    expect(
      form.getByRole("button", { name: "Save" }),
    ).toHaveAccessibleDescription("Fix the fields marked in red first");
  });

  it("shows a 422 next to its field", async () => {
    PUT.mockImplementation(() =>
      Promise.reject(
        apiError(422, "cycle: T02 → T03 → T02", { field: "meta.depends_on" }),
      ),
    );
    const { form } = await edit("T02");
    await userEvent.click(form.getByRole("checkbox", { name: /T03/ }));
    await userEvent.click(form.getByRole("button", { name: "Save" }));
    const deps = within(form.getByRole("group", { name: "Depends on" }));
    expect(await deps.findByRole("alert")).toHaveTextContent(
      "cycle: T02 → T03 → T02",
    );
  });

  it("shows the bar on 412, and Keep mine saves only after the click", async () => {
    const { form } = await edit("T02");
    state.etags.T02 = '"T02-2"'; // someone saved the file meanwhile
    await userEvent.type(form.getByRole("textbox", { name: "Title" }), "!");
    await userEvent.click(form.getByRole("button", { name: "Save" }));
    const bar = await form.findByRole("alert");
    expect(bar).toHaveTextContent("Changed on disk");
    expect(PUT).toHaveBeenCalledTimes(1);
    expect(state.tickets.find((t) => t.id === "T02")?.meta.title).toBe(
      "Ticket T02",
    );

    await userEvent.click(
      within(bar).getByRole("button", { name: "Keep mine" }),
    );
    expect(PUT).toHaveBeenCalledTimes(2);
    expect(PUT.mock.calls[1]?.[1].params.header).toEqual({
      "if-match": '"T02-2"',
    });
    expect(state.tickets.find((t) => t.id === "T02")?.meta.title).toBe(
      "Ticket T02!",
    );
  });

  it("Reload reads the file again and drops the edit", async () => {
    const { form, drawer } = await edit("T02");
    state.etags.T02 = '"T02-2"';
    state.tickets = state.tickets.map((t) =>
      t.id === "T02"
        ? { ...t, meta: { ...t.meta, title: "Changed outside" } }
        : t,
    );
    await userEvent.type(form.getByRole("textbox", { name: "Title" }), "!");
    await userEvent.click(form.getByRole("button", { name: "Save" }));
    await userEvent.click(
      within(await form.findByRole("alert")).getByRole("button", {
        name: "Reload",
      }),
    );
    await vi.waitFor(() => {
      expect(drawer.getByRole("textbox", { name: "Title" })).toHaveValue(
        "Changed outside",
      );
    });
    expect(PUT).toHaveBeenCalledTimes(1);
  });

  it("asks before Cancel drops changes", async () => {
    const { form, drawer } = await edit("T02");
    await userEvent.click(form.getByRole("button", { name: "Cancel" }));
    expect(drawer.queryByRole("form")).toBeNull(); // nothing changed: no question

    await userEvent.click(drawer.getByRole("button", { name: "Edit" }));
    const again = within(await drawer.findByRole("form", { name: "Edit T02" }));
    await userEvent.type(again.getByRole("textbox", { name: "Scope" }), "more");
    await userEvent.click(again.getByRole("button", { name: "Cancel" }));
    const confirm = within(
      screen.getByRole("dialog", { name: "Discard your changes?" }),
    );
    await userEvent.click(confirm.getByRole("button", { name: "Keep going" }));
    expect(drawer.getByRole("form", { name: "Edit T02" })).toBeVisible();

    await userEvent.click(again.getByRole("button", { name: "Cancel" }));
    await userEvent.click(
      within(
        screen.getByRole("dialog", { name: "Discard your changes?" }),
      ).getByRole("button", { name: "Discard changes" }),
    );
    expect(drawer.queryByRole("form")).toBeNull();
    expect(PUT).not.toHaveBeenCalled();
  });

  it("asks before ✕ closes with unsaved changes", async () => {
    const onClose = vi.fn();
    render(
      <QueryClientProvider client={new QueryClient()}>
        <TicketDrawer
          project="demo"
          ticketId="T02"
          onOpen={vi.fn()}
          onClose={onClose}
          onShowRun={vi.fn()}
        />
      </QueryClientProvider>,
    );
    const drawer = within(screen.getByRole("complementary"));
    await vi.waitFor(() => {
      expect(drawer.getByRole("button", { name: "Edit" })).toBeEnabled();
    });
    await userEvent.click(drawer.getByRole("button", { name: "Edit" }));
    await userEvent.type(
      await drawer.findByRole("textbox", { name: "Title" }),
      "!",
    );
    await userEvent.click(drawer.getByRole("button", { name: "Close" }));
    expect(onClose).not.toHaveBeenCalled();
    await userEvent.click(
      screen.getByRole("button", { name: "Discard changes" }),
    );
    expect(onClose).toHaveBeenCalled();
  });
});

describe("gate and review lines", () => {
  it("sums up a blocked attempt's gates, before any review", async () => {
    const { drawer } = show("T04");
    const needs = await drawer.findByText("Why it needs you");
    const box = within(needs.parentElement as HTMLElement);
    const checks = await box.findByRole("list", { name: "Attempt 3 checks" });
    expect(
      within(checks)
        .getAllByRole("listitem")
        .map((li) => li.textContent),
    ).toEqual(["Gates: 2 of 3 passed · test failed", "Review: not run"]);
    // Next to the latest attempt too.
    const attempts = drawer.getByRole("region", { name: "Attempts" });
    expect(
      await within(attempts).findByText("Gates: 2 of 3 passed · test failed"),
    ).toBeInTheDocument();
  });

  it("sums up the reviewer's verdict with the items met", async () => {
    state.reports = {
      gates: {
        passed: true,
        stopped: null,
        results: [
          gate("install", "passed"),
          gate("lint", "skipped"),
          gate("test", "timed_out"),
        ],
      },
      review: {
        verdict: "changes_requested",
        summary: "",
        stopped: null,
        items: [
          { text: "a", met: true, reason: "" },
          { text: "b", met: true, reason: "" },
          { text: "c", met: true, reason: "" },
          { text: "d", met: true, reason: "" },
          { text: "e", met: false, reason: "" },
        ],
      },
    };
    const { drawer } = show("T06");
    const checks = await drawer.findAllByRole("list", {
      name: "Attempt 3 checks",
    });
    expect(
      within(checks[0] as HTMLElement)
        .getAllByRole("listitem")
        .map((li) => li.textContent),
    ).toEqual([
      "Gates: 1 of 2 passed · test timed out",
      "Review: changes requested · 4 of 5 met",
    ]);
  });
});
