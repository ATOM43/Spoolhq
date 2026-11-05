import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter } from "react-router";
import { RouterProvider } from "react-router/dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ProjectDetail } from "@/entities/project";
import type { Schemas } from "@/shared/api";
import {
  api,
  DaemonError,
  getDaemonInfo,
  getHealth,
  getVersion,
  subscribeEvents,
} from "@/shared/api";

import { SET_UP_FIRST } from "@/features/settings";

import { ProjectPage } from "./ProjectPage";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return {
    ...actual,
    api: { GET: vi.fn(), POST: vi.fn(), PUT: vi.fn() },
    subscribeEvents: vi.fn(),
    getDaemonInfo: vi.fn(),
    getHealth: vi.fn(),
    getVersion: vi.fn(),
  };
});

type Handler = (path: string, init?: unknown) => unknown;
const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;

const ok = (data: unknown) =>
  Promise.resolve({ data, response: new Response() });

const PROBLEM = {
  file: "/w/demo/project.yaml",
  field: "merge_policy.max_diff_lines",
  message: "must be greater than 0",
};

type Job = Schemas["JobView"];

let detail: ProjectDetail;
let job: Job;

const JOB_ID = "a".repeat(32);

function creationJob(
  state: Job["state"],
  commands: Job["steps"][number]["state"] = "running",
): Job {
  const step = (
    name: Job["steps"][number]["name"],
    title: string,
    stepState: Job["steps"][number]["state"],
  ) => ({
    name,
    title,
    state: stepState,
    duration_s: null,
    passed: [],
    message: stepState === "failed" ? "The test command failed" : null,
    output: stepState === "failed" ? "FAILED test_example" : null,
    field: stepState === "failed" ? "commands.test" : null,
  });
  return {
    id: JOB_ID,
    project: "demo",
    source: "empty",
    state,
    steps: [
      step("workspace", "Create workspace", "passed"),
      step("repo", "Prepare repo", "passed"),
      step("commands", "Check commands", commands),
      step("commit", "Initial commit", "pending"),
    ],
    rollback:
      state === "running" ? null : { removed: ["/code/demo"], left: [] },
  };
}

const CREATING = {
  run_state: "creating",
  job_id: JOB_ID,
  repo: null,
  default_branch: null,
  has_spec: false,
};

function project(extra: Partial<ProjectDetail> = {}): ProjectDetail {
  return {
    name: "demo",
    done: 0,
    total: 0,
    run_state: "idle",
    needs_you: 0,
    latest_seq: 0,
    draft: 0,
    remaining_h: 0,
    has_spec: true,
    repo: "/code/demo",
    default_branch: "main",
    remote: null,
    invalid_tickets: 0,
    next_ticket: null,
    idle: null,
    ...extra,
  };
}

function showPanel(path = "/p/demo") {
  const router = createMemoryRouter(
    [{ path: "/p/:id", element: <ProjectPage /> }],
    { initialEntries: [path] },
  );
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

const LOGGED_IN = {
  name: "claude-code-cli",
  installed: true,
  logged_in: true,
  reason: null,
};
let backends: (typeof LOGGED_IN)[] = [];

const projectCalls = () =>
  GET.mock.calls.filter(([path]) => path === "/api/projects/{name}").length;

describe("project panel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getDaemonInfo).mockResolvedValue({
      port: 8765,
      tokenPresent: true,
      tokenPath: "/t",
    });
    vi.mocked(getHealth).mockResolvedValue({ status: "ok" });
    vi.mocked(getVersion).mockResolvedValue({ version: "0.0.0" });
    vi.mocked(subscribeEvents).mockReturnValue(() => undefined);
    detail = project();
    backends = [LOGGED_IN];
    GET.mockImplementation((path) => {
      if (path === "/api/projects/{name}") {
        return ok(detail);
      }
      if (path === "/api/jobs/{job_id}") {
        return ok(job);
      }
      if (path === "/api/agents") {
        return ok({
          backends,
          graphify: { installed: false, version: null, tested: false },
        });
      }
      if (path === "/api/settings") {
        return ok({ secrets: { anthropic: { set: false, source: null } } });
      }
      if (path === "/api/projects/{name}/spec") {
        return ok({ content: "# Objective" });
      }
      if (path === "/api/projects/{name}/runs/current") {
        return detail.settings_error
          ? Promise.reject(
              new DaemonError({
                kind: "api",
                status: 422,
                code: "validation_error",
                message: "project.yaml: invalid",
                field: null,
                etag: null,
                current: null,
              }),
            )
          : ok({
              project: "demo",
              active: false,
              working: false,
              run: null,
              attempts: 0,
              input_tokens: 0,
              output_tokens: 0,
              phases: [],
            });
      }
      throw new Error(`unexpected GET ${path}`);
    });
  });

  it("shows the breadcrumb, repo, branch, remote and guidance", async () => {
    showPanel();
    expect(
      await screen.findByRole("heading", { name: "demo" }),
    ).toBeInTheDocument();
    const crumbs = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(within(crumbs).getByRole("link", { name: "Home" })).toHaveAttribute(
      "href",
      "/",
    );
    expect(screen.getByText("/code/demo")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Copy repository path" }),
    ).toBeInTheDocument();
    expect(screen.getByText("main")).toBeInTheDocument();
    expect(screen.getByText("Local git · no remote")).toBeInTheDocument();
    expect(
      screen.getByText("No plan yet · write the spec, then generate a plan"),
    ).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Tickets 0" })).toBeInTheDocument();
  });

  it("shows Creating… and the live checklist while the project is created, then Spec", async () => {
    detail = project(CREATING);
    job = creationJob("running");
    showPanel();
    const checklist = await screen.findByRole("region", {
      name: "Creating the project",
    });
    expect(screen.getByText("Creating…")).toBeInTheDocument();
    expect(
      checklist.querySelector('[data-step="commands"][data-state="running"]'),
    ).not.toBeNull();
    expect(screen.queryByRole("tab")).toBeNull();
    expect(subscribeEvents).not.toHaveBeenCalled();
    const read = GET.mock.calls.map(([path]) => path);
    expect(read).not.toContain("/api/projects/{name}/spec");
    expect(read).not.toContain("/api/projects/{name}/runs/current");

    detail = project({ has_spec: false });
    job = creationJob("succeeded", "passed");
    const spec = await screen.findByRole(
      "tab",
      { name: "Spec" },
      { timeout: 3000 },
    );
    expect(spec).toHaveAttribute("aria-selected", "true");
    expect(screen.queryByText("Creating…")).toBeNull();
  });

  it("says the project wasn't created when its creation fails", async () => {
    detail = project(CREATING);
    job = creationJob("failed", "failed");
    showPanel();
    expect(
      await screen.findByText("This project wasn't created"),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Home" })).toHaveAttribute(
      "href",
      "/",
    );
    expect(screen.getByText("FAILED test_example")).toBeInTheDocument();
    expect(screen.queryByRole("tab")).toBeNull();
  });

  it("opens on the tab the link asks for", async () => {
    showPanel("/p/demo?tab=run");
    expect(
      await screen.findByRole("tab", { name: "Run", selected: true }),
    ).toBeInTheDocument();
  });

  it("shows a red bar naming the invalid field, and Reload refetches", async () => {
    detail = project({
      repo: null,
      default_branch: null,
      settings_error: PROBLEM,
    });
    showPanel();
    const bar = await screen.findByRole("alert");
    expect(bar).toHaveTextContent(
      "project.yaml: merge_policy.max_diff_lines: must be greater than 0",
    );
    expect(bar).toHaveTextContent("/w/demo/project.yaml");
    expect(
      within(bar).getByRole("button", { name: "Copy settings file path" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Run next/ })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: /^Run next/ }),
    ).toHaveAccessibleDescription("Fix project.yaml first");

    detail = project();
    const before = projectCalls();
    await userEvent.click(within(bar).getByRole("button", { name: "Reload" }));
    await waitFor(() => {
      expect(projectCalls()).toBe(before + 1);
    });
    await waitFor(() => {
      expect(screen.queryByText(/merge_policy/)).toBeNull();
    });
  });

  it("opens Settings from the gear, also with an invalid project.yaml", async () => {
    detail = project({ settings_error: PROBLEM });
    showPanel();
    await screen.findByRole("alert");
    const gear = screen.getByRole("button", { name: "Settings" });
    expect(gear).toBeEnabled();
    await userEvent.click(gear);
    const dialog = screen.getByRole("dialog", { name: "Settings" });
    expect(
      within(dialog).getByRole("tab", { name: "Agents", selected: true }),
    ).toBeInTheDocument();
    await userEvent.click(within(dialog).getByRole("button", { name: "Done" }));
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("links a 'set up an agent' reason to Settings on the Agents tab", async () => {
    backends = [{ ...LOGGED_IN, logged_in: false }];
    detail = project({ total: 3, next_ticket: "T01" });
    showPanel();
    // Re-rendered disabled once the agents answer, so look it up each time.
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /^Run next/ }),
      ).toHaveAccessibleDescription(SET_UP_FIRST);
    });
    await userEvent.click(
      screen.getAllByRole("button", {
        name: "Open Settings",
      })[0] as HTMLElement,
    );
    const dialog = screen.getByRole("dialog", { name: "Settings" });
    expect(
      within(dialog).getByRole("tab", { name: "Agents", selected: true }),
    ).toBeInTheDocument();
  });
});
