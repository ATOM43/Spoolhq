import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter } from "react-router";
import { RouterProvider } from "react-router/dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  api,
  DaemonError,
  getDaemonInfo,
  getHealth,
  getVersion,
  subscribeEvents,
  type EventEnvelope,
  type Schemas,
} from "@/shared/api";

import { HomePage } from "./HomePage";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return {
    ...actual,
    api: { GET: vi.fn(), POST: vi.fn(), PUT: vi.fn() },
    subscribeEvents: vi.fn(),
    getDaemonInfo: vi.fn(),
    getHealth: vi.fn(),
    getVersion: vi.fn(),
    pickFolder: vi.fn(),
  };
});

type Project = Schemas["ProjectSummary"];
type Handler = (path: string, init?: unknown) => unknown;

const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;
const POST = vi.mocked(api.POST) as unknown as ReturnType<
  typeof vi.fn<Handler>
>;

function project(name: string, extra: Partial<Project> = {}): Project {
  return {
    name,
    done: 0,
    total: 3,
    run_state: "idle",
    needs_you: 0,
    latest_seq: 0,
    draft: 0,
    remaining_h: 0,
    has_spec: true,
    ...extra,
  };
}

type Run = NonNullable<Project["run"]>;

function run(extra: Partial<Run> = {}): Run {
  return {
    id: 1,
    kind: "ticket",
    ticket_id: "T01",
    status: "running",
    reason: null,
    started_at: "2026-11-05T10:00:00Z",
    ended_at: null,
    reset_at: null,
    progress_note: null,
    ...extra,
  };
}

function ticket(id: string, title: string, status: string) {
  return { id, file_name: `${id}.md`, meta: { id, title, status }, body: "" };
}

const ok = (data: unknown) =>
  Promise.resolve({ data, response: new Response() });
const notRunning = () =>
  new DaemonError({ kind: "not_running", port: 8765, message: "refused" });

let projects: Project[] = [];
let tickets: Record<string, unknown[]> = {};

function daemonUp() {
  vi.mocked(getDaemonInfo).mockResolvedValue({
    port: 8765,
    tokenPresent: true,
    tokenPath: "/t",
  });
  vi.mocked(getHealth).mockResolvedValue({ status: "ok" });
  vi.mocked(getVersion).mockResolvedValue({ version: "0.0.0" });
}

function daemonDown() {
  daemonUp();
  vi.mocked(getHealth).mockRejectedValue(notRunning());
}

function renderHome() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const router = createMemoryRouter(
    [
      { path: "/", element: <HomePage /> },
      { path: "/p/:id", element: <p>Project panel</p> },
    ],
    { initialEntries: ["/"] },
  );
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

const projectCalls = () =>
  GET.mock.calls.filter(([path]) => path === "/api/projects").length;

describe("Home", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    daemonUp();
    projects = [];
    tickets = {};
    GET.mockImplementation((path, init) => {
      if (path === "/api/projects") {
        return ok(projects);
      }
      if (path === "/api/projects/{name}/tickets") {
        const name = (init as { params: { path: { name: string } } }).params
          .path.name;
        return ok({ tickets: tickets[name] ?? [], invalid: [] });
      }
      if (path === "/api/templates") {
        return ok([]);
      }
      throw new Error(`unexpected GET ${path}`);
    });
    vi.mocked(subscribeEvents).mockReturnValue(() => undefined);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows a loading state while the projects load", async () => {
    GET.mockReturnValue(new Promise(() => undefined));
    renderHome();
    expect(await screen.findByText("Loading projects…")).toBeInTheDocument();
  });

  it("shows an empty state whose button opens New project", async () => {
    renderHome();
    const empty = (await screen.findByText("No projects yet")).parentElement;
    if (empty === null) {
      throw new Error("no empty state");
    }
    await userEvent.click(
      within(empty).getByRole("button", { name: "New project" }),
    );
    expect(screen.getByRole("dialog", { name: "New project" })).toBeVisible();
  });

  it("shows an error state with a retry that recovers", async () => {
    const usual = GET.getMockImplementation();
    let failed = false;
    GET.mockImplementation((path, init) => {
      if (path !== "/api/projects" || failed) {
        return usual?.(path, init);
      }
      failed = true;
      return Promise.reject(
        new DaemonError({
          kind: "api",
          status: 500,
          code: "internal",
          message: "Something broke.",
          field: null,
          etag: null,
          current: null,
        }),
      );
    });
    projects = [project("demo")];
    renderHome();
    expect(
      await screen.findByRole("heading", {
        name: "Couldn't load the projects",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Something broke.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("demo")).toBeInTheDocument();
  });

  it("lists projects as cards with progress, status, activity and usage", async () => {
    projects = [
      project("alpha", {
        done: 13,
        total: 18,
        remaining_h: 12,
        run_state: "running",
        run: run({ ticket_id: "T15" }),
        run_step: "implement",
        template: "fastapi-react",
        usage: { tokens: 0, cost_usd: 9.852 },
      }),
      project("beta", {
        done: 2,
        total: 2,
        last_activity: new Date(Date.now() - 12 * 60_000).toISOString(),
        usage: { tokens: 182_000, cost_usd: null },
      }),
      project("gamma", { total: 0, has_spec: false }),
    ];
    renderHome();
    const alpha = await screen.findByRole("link", { name: /alpha/ });
    expect(alpha).toHaveTextContent("13 of 18 done · 12 h left");
    expect(alpha).toHaveTextContent("Running T15 · Implement");
    expect(alpha).toHaveTextContent("fastapi-react");
    expect(alpha).toHaveTextContent("Active now · $9.85");
    expect(alpha.querySelector("svg")).not.toBeNull();
    const beta = screen.getByRole("link", { name: /beta/ });
    expect(beta).toHaveTextContent("All done");
    expect(beta).toHaveTextContent("existing repo");
    expect(beta).toHaveTextContent("12 min ago · 182k tokens");
    const gamma = screen.getByRole("link", { name: /gamma/ });
    expect(gamma).toHaveTextContent("No tickets yet");
    expect(gamma).toHaveTextContent("No spec yet");
    expect(screen.getByText("3 projects")).toBeInTheDocument();
    await userEvent.click(alpha);
    expect(await screen.findByText("Project panel")).toBeInTheDocument();
  });

  it("shows Settings invalid with the first error, never Unknown", async () => {
    projects = [
      project("broken", {
        run_state: "unknown",
        settings_error: {
          file: "/w/broken/project.yaml",
          field: "merge_policy.max_diff_lines",
          message: "must be greater than 0",
        },
      }),
      project("fine"),
    ];
    renderHome();
    const card = await screen.findByRole("link", { name: /broken/ });
    expect(card).toHaveTextContent("Settings invalid");
    expect(card).toHaveTextContent(
      "project.yaml: merge_policy.max_diff_lines: must be greater than 0",
    );
    expect(screen.getByRole("link", { name: /fine/ })).toHaveTextContent(
      "Idle",
    );
    expect(screen.queryByText(/Unknown/)).toBeNull();
  });

  it("shows a project being created as Creating…, with no Needs-you card", async () => {
    projects = [
      // What the daemon reports while a creation job holds the project; even a
      // half-written project.yaml is never reported as invalid then.
      project("fresh", {
        run_state: "creating",
        job_id: "a".repeat(32),
        total: 0,
        draft: 2, // would be a "Draft plan" card for any other project
      }),
    ];
    renderHome();
    const card = await screen.findByRole("link", { name: /fresh/ });
    const status = within(card).getByText("Creating…");
    expect(status).toHaveAttribute("data-status", "creating");
    expect(status.querySelector("svg.animate-spin")).not.toBeNull();
    expect(card).not.toHaveTextContent("Settings invalid");
    expect(screen.queryByRole("region", { name: /Needs you/ })).toBeNull();
    expect(subscribeEvents).not.toHaveBeenCalled();
  });

  it("shows a rollback that left paths behind as a card that Dismiss hides", async () => {
    const job = "b".repeat(32);
    projects = [
      project("alpha"),
      project("broken", {
        run_state: "cleanup_failed",
        job_id: job,
        left: ["/code/broken"],
        total: 0,
      }),
    ];
    POST.mockImplementation(() => {
      projects = [project("alpha")];
      return Promise.resolve({ response: new Response(null, { status: 204 }) });
    });
    renderHome();
    const card = await screen.findByRole("article", {
      name: "Cleanup failed: broken",
    });
    expect(card).toHaveTextContent("Couldn't clean up broken");
    expect(card).toHaveTextContent("/code/broken");
    // Only a card: no project card, no event stream for it.
    expect(screen.queryByRole("link", { name: /broken/ })).toBeNull();
    expect(screen.getByText("1 project")).toBeInTheDocument();
    expect(subscribeEvents).toHaveBeenCalledTimes(1);

    await userEvent.click(
      within(card).getByRole("button", { name: "Dismiss" }),
    );
    expect(POST).toHaveBeenCalledWith("/api/jobs/{job_id}/dismiss", {
      params: { path: { job_id: job } },
    });
    await waitFor(() => {
      expect(screen.queryByRole("region", { name: /Needs you/ })).toBeNull();
    });
  });

  it("shows a 'Needs you' card for each kind, with its action", async () => {
    projects = [
      project("alpha", {
        needs_you: 2,
        run: run({
          ticket_id: "T10",
          status: "blocked",
          reason: "gates failed 3 times",
          ended_at: new Date(Date.now() - 12 * 60_000).toISOString(),
        }),
      }),
      project("beta", { draft: 24, total: 24, remaining_h: 61 }),
      project("gamma", {
        run: run({
          ticket_id: "T04",
          status: "interrupted",
          reason: "the daemon stopped",
        }),
      }),
      project("delta", {
        run_state: "paused",
        run: run({
          ticket_id: "T02",
          status: "paused",
          reset_at: "2026-11-05T14:30:00Z",
        }),
      }),
      project("epsilon"),
    ];
    tickets = {
      alpha: [
        ticket("T10", "Context pack", "blocked"),
        ticket("T12", "Reviewer agent", "awaiting_approval"),
        ticket("T03", "Done one", "done"),
      ],
      gamma: [ticket("T04", "Fix cache", "running")],
    };
    POST.mockImplementation(() => ok({}));
    renderHome();
    const section = await screen.findByRole("region", { name: /Needs you/ });
    const card = (name: RegExp) =>
      within(section).getByRole("article", { name });
    await within(section).findByText("Context pack");

    const blocked = card(/Blocked: alpha T10/);
    expect(blocked).toHaveTextContent("Gates failed 3 times");
    expect(blocked).toHaveTextContent("12 min ago");
    expect(
      within(blocked).getByRole("link", { name: "Unblock" }),
    ).toHaveAttribute("href", "/p/alpha?tab=tickets&ticket=T10");
    expect(
      within(card(/Needs approval: alpha T12/)).getByRole("link", {
        name: "Review",
      }),
    ).toHaveAttribute("href", "/p/alpha?tab=tickets&ticket=T12");
    const plan = card(/Plan ready: beta/);
    expect(plan).toHaveTextContent("Planner finished: 24 tickets · 61 h");
    expect(
      within(plan).getByRole("link", { name: "Review plan" }),
    ).toHaveAttribute("href", "/p/beta?tab=tickets");
    expect(
      within(card(/Paused · usage limit: delta T02/)).getByRole("link", {
        name: "Open run",
      }),
    ).toHaveAttribute("href", "/p/delta?tab=run&ticket=T02");
    const interrupted = card(/Interrupted: gamma T04/);
    expect(interrupted).toHaveTextContent("Fix cache");
    await userEvent.click(
      within(interrupted).getByRole("button", { name: "Resume" }),
    );
    expect(POST).toHaveBeenCalledWith(
      "/api/projects/{name}/run/ticket/{ticket_id}",
      { params: { path: { name: "gamma", ticket_id: "T04" } } },
    );
    await userEvent.click(
      within(interrupted).getByRole("button", { name: "Discard" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Discard run" }));
    expect(POST).toHaveBeenCalledWith(
      "/api/projects/{name}/tickets/{ticket_id}/discard",
      { params: { path: { name: "gamma", ticket_id: "T04" } } },
    );
    expect(within(section).getAllByRole("article")).toHaveLength(5);
    expect(within(section).queryByText(/Done one/)).toBeNull();
  });

  it("hides 'Needs you' when nothing needs the user", async () => {
    projects = [
      project("alpha"),
      project("beta", { run_state: "paused", run: run({ status: "paused" }) }),
    ];
    renderHome();
    await screen.findByRole("link", { name: /alpha/ });
    expect(screen.queryByRole("region", { name: /Needs you/ })).toBeNull();
  });

  it("updates progress from a run event without a refetch loop", async () => {
    projects = [project("demo", { done: 0, total: 3 })];
    renderHome();
    expect(await screen.findByText("0 of 3 done")).toBeInTheDocument();
    expect(subscribeEvents).toHaveBeenCalledTimes(1);
    const [options, onEvent] = vi.mocked(subscribeEvents).mock.calls[0] ?? [];
    expect(options?.project).toBe("demo");

    projects = [project("demo", { done: 1, total: 3 })];
    const event = (seq: number, type: string): EventEnvelope => ({
      seq,
      run_id: 1,
      attempt: null,
      ticket: "T01",
      type,
      ts: "",
      data: {},
    });
    act(() => {
      onEvent?.(event(10, "agent.message")); // not about progress
      onEvent?.(event(11, "run.status"));
      onEvent?.(event(12, "integrate"));
    });
    expect(await screen.findByText("1 of 3 done")).toBeInTheDocument();
    await new Promise((resolve) => setTimeout(resolve, 600));
    expect(projectCalls()).toBe(2); // the first load and one refetch, no polling
    expect(subscribeEvents).toHaveBeenCalledTimes(1);
  });

  it("shows how to start a missing daemon, then loads by itself when it is back", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    daemonDown();
    projects = [project("demo")];
    renderHome();
    expect(
      await screen.findByRole("heading", { name: "The daemon isn't running" }),
    ).toBeInTheDocument();
    expect(screen.getByText("spool serve")).toBeInTheDocument();
    expect(projectCalls()).toBe(0);

    daemonUp();
    await act(() => vi.advanceTimersByTimeAsync(3000));
    expect(await screen.findByText("demo")).toBeInTheDocument();
    expect(screen.queryByText("The daemon isn't running")).toBeNull();
  });

  it("shows a project being created in the list without a reload", async () => {
    POST.mockImplementation(() => {
      projects = [project("fresh", { total: 0, run_state: "creating" })];
      return ok({ job_id: "j1" });
    });
    renderHome();
    await screen.findByText("No projects yet");
    // The header's button; the empty state has one too.
    const [newProject] = screen.getAllByRole("button", { name: "New project" });
    if (newProject === undefined) {
      throw new Error("no New project button");
    }
    await userEvent.click(newProject);
    const dialog = screen.getByRole("dialog", { name: "New project" });
    await userEvent.click(
      within(dialog).getByRole("radio", { name: "Empty repo" }),
    );
    await userEvent.type(
      within(dialog).getByLabelText("Project name"),
      "fresh",
    );
    await userEvent.type(
      within(dialog).getByLabelText("Repo folder"),
      "/repos/fresh",
    );
    const steps = ["passed", "running", "pending", "pending"].map((state) => ({
      name: "workspace",
      title: "Step",
      state,
      duration_s: null,
      passed: [],
      message: null,
      output: null,
      field: null,
    }));
    GET.mockImplementation((path) =>
      path === "/api/projects"
        ? ok(projects)
        : path === "/api/jobs/{job_id}"
          ? ok({
              id: "j1",
              project: "fresh",
              source: "empty",
              state: "running",
              steps,
            })
          : ok([]),
    );
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Create project" }),
    );
    await waitFor(() => {
      expect(screen.getByRole("link", { name: /fresh/ })).toHaveTextContent(
        "Creating…",
      );
    });
  });
});
