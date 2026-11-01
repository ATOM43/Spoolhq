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

  it("lists projects with progress and status, and opens one", async () => {
    projects = [
      project("alpha", { done: 1, total: 4, run_state: "running" }),
      project("beta", { done: 2, total: 2 }),
      project("gamma", { total: 0 }),
    ];
    renderHome();
    const alpha = await screen.findByRole("link", { name: /alpha/ });
    expect(alpha).toHaveTextContent("1 of 4 tickets done");
    expect(alpha).toHaveTextContent("Running");
    expect(alpha.querySelector("svg")).not.toBeNull();
    expect(screen.getByRole("link", { name: /beta/ })).toHaveTextContent(
      "Done",
    );
    expect(screen.getByRole("link", { name: /gamma/ })).toHaveTextContent(
      "No plan yet",
    );
    await userEvent.click(alpha);
    expect(await screen.findByText("Project panel")).toBeInTheDocument();
  });

  it("lists each kind of 'Needs you' once, linking to its project", async () => {
    projects = [
      project("alpha", { needs_you: 2 }),
      project("beta", { needs_you: 1, run_state: "paused" }),
      project("gamma"),
    ];
    tickets = {
      alpha: [
        ticket("T01", "Parse slugs", "blocked"),
        ticket("T02", "Add login", "awaiting_approval"),
        ticket("T03", "Done one", "done"),
      ],
      beta: [ticket("T04", "Fix cache", "blocked")],
    };
    renderHome();
    const section = await screen.findByRole("region", { name: "Needs you" });
    await within(section).findByText("T01 · Parse slugs");
    for (const name of ["Blocked", "Awaiting approval", "Paused runs"]) {
      expect(within(section).getAllByRole("heading", { name })).toHaveLength(1);
    }
    expect(within(section).getByText("T04 · Fix cache")).toBeInTheDocument();
    expect(within(section).getByText("Run paused")).toBeInTheDocument();
    expect(within(section).queryByText(/Done one/)).toBeNull();
    const links = within(section).getAllByRole("link");
    expect(links.map((link) => link.getAttribute("href"))).toEqual([
      "/p/alpha",
      "/p/beta",
      "/p/alpha",
      "/p/beta",
    ]);
    expect(
      GET.mock.calls.filter(([path]) => path.endsWith("/tickets")),
    ).toHaveLength(2); // gamma needs nothing, so its tickets aren't fetched
  });

  it("updates progress from a run event without a refetch loop", async () => {
    projects = [project("demo", { done: 0, total: 3 })];
    renderHome();
    expect(await screen.findByText("0 of 3 tickets done")).toBeInTheDocument();
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
    expect(await screen.findByText("1 of 3 tickets done")).toBeInTheDocument();
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

  it("shows a created project in the list without a reload", async () => {
    POST.mockImplementation(() => {
      projects = [project("fresh", { total: 0 })];
      return ok({ name: "fresh", path: "/w/fresh", missing_notes: [] });
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
    await userEvent.type(within(dialog).getByLabelText("Name"), "fresh");
    await userEvent.type(
      within(dialog).getByLabelText("Repository folder"),
      "/repos/fresh",
    );
    GET.mockImplementation((path) =>
      path === "/api/projects"
        ? ok(projects)
        : path === "/api/projects/{name}/settings"
          ? ok({ settings: { commands: {} } })
          : ok([]),
    );
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Create project" }),
    );
    await waitFor(() => {
      expect(screen.getByRole("link", { name: /fresh/ })).toBeInTheDocument();
    });
  });
});
