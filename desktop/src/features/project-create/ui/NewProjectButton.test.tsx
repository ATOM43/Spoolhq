import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, useLocation } from "react-router";
import { RouterProvider } from "react-router/dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api, DaemonError, pickFolder, type Schemas } from "@/shared/api";
import { Toaster } from "@/shared/ui";

import { DIRTY_REASON, NAME_RULE } from "../model/form";
import { CHECKS_HELP } from "./Checklist";
import { CREATED_TOAST, NewProjectButton } from "./NewProjectButton";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return {
    ...actual,
    api: { GET: vi.fn(), POST: vi.fn() },
    pickFolder: vi.fn(),
  };
});

type Handler = (path: string, init?: unknown) => unknown;
const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;
const POST = vi.mocked(api.POST) as unknown as ReturnType<
  typeof vi.fn<Handler>
>;
type Job = Schemas["JobView"];
type Step = Schemas["StepView"];

const ok = (data: unknown) =>
  Promise.resolve({ data, response: new Response() });
const JOB_ID = "a".repeat(32);
const TEMPLATE = {
  name: "fastapi-react",
  description: "A FastAPI and React stack.",
  summary: "FastAPI · SQLAlchemy · pytest · React",
  commands: { install: "just install", lint: "just lint", test: "just test" },
};
const NAMES = ["workspace", "repo", "commands", "commit"] as const;
const TITLES = [
  "Create workspace",
  "Prepare repo",
  "Check commands",
  "Initial commit",
];

function job(
  state: Job["state"],
  steps: [Step["state"], Partial<Step>?][],
  extra: Partial<Job> = {},
): Job {
  return {
    id: JOB_ID,
    project: "demo",
    source: "template",
    state,
    rollback: null,
    steps: steps.map(([stepState, more], index) => ({
      name: NAMES[index] ?? "commit",
      title: TITLES[index] ?? "",
      state: stepState,
      duration_s: null,
      passed: [],
      message: null,
      output: null,
      field: null,
      ...more,
    })),
    ...extra,
  };
}

const RUNNING = job("running", [
  ["passed"],
  ["passed"],
  ["running", { passed: ["install", "lint"] }],
  ["pending"],
]);

let jobReply: Job = RUNNING;

function Panel() {
  const location = useLocation();
  return <p>Panel at {location.pathname + location.search}</p>;
}

function renderButton() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const router = createMemoryRouter(
    [
      { path: "/", element: <NewProjectButton /> },
      { path: "/p/:id", element: <Panel /> },
    ],
    { initialEntries: ["/"] },
  );
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
      <Toaster />
    </QueryClientProvider>,
  );
}

async function openDialog() {
  renderButton();
  await userEvent.click(screen.getByRole("button", { name: "New project" }));
  const dialog = screen.getByRole("dialog", { name: "New project" });
  await within(dialog).findByText("fastapi-react");
  return dialog;
}

async function fill(name: string, repo = "/home/me/code/demo") {
  await userEvent.type(screen.getByLabelText("Project name"), name);
  await userEvent.type(screen.getByLabelText("Repo folder"), repo);
}

const create = () => screen.getByRole("button", { name: "Create project" });
const jobPolls = () =>
  GET.mock.calls.filter(([path]) => path === "/api/jobs/{job_id}").length;
const requestBody = () =>
  (POST.mock.calls[0]?.[1] as { body: Record<string, unknown> }).body;

describe("New project", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    jobReply = RUNNING;
    GET.mockImplementation((path) => {
      if (path === "/api/templates") {
        return ok([TEMPLATE]);
      }
      if (path === "/api/settings") {
        return ok({ projects_dir: "/home/me/spoolhq-projects" });
      }
      if (path === "/api/jobs/{job_id}") {
        return ok(jobReply);
      }
      throw new Error(`unexpected GET ${path}`);
    });
    POST.mockImplementation((path) => {
      if (path === "/api/projects") {
        return ok({ job_id: JOB_ID });
      }
      if (path === "/api/jobs/{job_id}/cancel") {
        return ok(
          job("cancelled", [["passed"], ["failed"], ["pending"], ["pending"]]),
        );
      }
      throw new Error(`unexpected POST ${path}`);
    });
  });

  it("shows the right fields and help text for each source", async () => {
    const dialog = await openDialog();
    expect(within(dialog).getByText("Bundled")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /fastapi-react/ })).toBeChecked();
    expect(
      screen.getByText("A new or empty folder; its parent must exist"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Filled in from the template. Gates run these on every ticket.",
      ),
    ).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("Project name"), "demo");
    expect(screen.getByLabelText("Workspace")).toHaveTextContent(
      "/home/me/spoolhq-projects/demo",
    );

    await userEvent.click(screen.getByRole("radio", { name: "Existing repo" }));
    expect(within(dialog).queryByText("fastapi-react")).toBeNull();
    expect(
      screen.getByText(
        "A clean git repository; the stack commands run on a temporary copy, never in your checkout",
      ),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("test")).toHaveValue("");
    expect(screen.getByLabelText("test")).toHaveAttribute(
      "placeholder",
      "e.g. just test",
    );
    expect(
      screen.getByText("Gates run these on every ticket."),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole("radio", { name: "Empty repo" }));
    expect(
      screen.getByText("A new or empty folder; its parent must exist"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Leave empty to set later in project.yaml. Gates run these on every ticket.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/merge policy: Direct unless risky/)).toBeVisible();
  });

  it("shows the name rule for VW and keeps Create disabled", async () => {
    await openDialog();
    await fill("VW");
    expect(screen.getByRole("alert")).toHaveTextContent(NAME_RULE);
    expect(create()).toBeDisabled();
    await userEvent.clear(screen.getByLabelText("Project name"));
    await userEvent.type(screen.getByLabelText("Project name"), "vw");
    expect(create()).toBeEnabled();
  });

  it("fills the commands in from the template", async () => {
    await openDialog();
    expect(screen.getByLabelText("install")).toHaveValue("just install");
    expect(screen.getByLabelText("lint")).toHaveValue("just lint");
    expect(screen.getByLabelText("test")).toHaveValue("just test");
  });

  it("creates an empty repo without commands", async () => {
    await openDialog();
    await userEvent.click(screen.getByRole("radio", { name: "Empty repo" }));
    await fill("demo");
    await userEvent.click(create());
    await waitFor(() => {
      expect(POST).toHaveBeenCalledWith("/api/projects", expect.anything());
    });
    expect(requestBody()).toEqual({
      name: "demo",
      source: "empty",
      repo_path: "/home/me/code/demo",
      template: null,
      commands: { install: null, lint: null, test: null },
      git_remote: null,
      merge_preset: "direct_unless_risky",
      clickup_list_id: null,
    });
  });

  it("puts a 422 next to its field, with no checklist", async () => {
    POST.mockImplementation(() =>
      Promise.reject(
        new DaemonError({
          kind: "api",
          status: 422,
          code: "validation_error",
          message: "The parent folder doesn't exist",
          field: "repo_path",
          etag: null,
          current: null,
        }),
      ),
    );
    await openDialog();
    await fill("demo");
    await userEvent.click(create());
    const repo = screen.getByLabelText("Repo folder");
    await waitFor(() => {
      expect(repo).toHaveAccessibleDescription(
        "The parent folder doesn't exist",
      );
    });
    expect(repo).toHaveAttribute("aria-invalid", "true");
    expect(
      screen.queryByRole("region", { name: "Creating the project" }),
    ).toBeNull();
    expect(repo).toBeEnabled();
  });

  it("shows each step's state while the job runs", async () => {
    await openDialog();
    await fill("demo");
    await userEvent.click(create());
    const list = await screen.findByRole("region", {
      name: "Creating the project",
    });
    const rows = within(list).getAllByRole("listitem");
    expect(rows.map((row) => row.textContent)).toEqual([
      "Create workspacePassed",
      "Generate from fastapi-reactPassed",
      "Check commands · 2 of 3 passedRunning",
      "Initial commitPending",
    ]);
    expect(screen.getByRole("button", { name: "Creating…" })).toBeDisabled();
    expect(screen.getByLabelText("Project name")).toBeDisabled();
    const [install, , test] = screen
      .getAllByText(/^(Passed|Running)$/)
      .filter((el) => !list.contains(el));
    expect(install).toHaveTextContent("Passed");
    expect(test).toHaveTextContent("Running");
  });

  it("shows a failed step's output and Fix focuses its field", async () => {
    jobReply = job(
      "failed",
      [
        ["passed"],
        ["passed"],
        [
          "failed",
          {
            passed: ["install", "lint"],
            message: "The test command failed",
            output: "FAILED tests/test_math.py::test_add",
            field: "commands.test",
          },
        ],
        ["pending"],
      ],
      { rollback: { removed: ["/home/me/code/demo"], left: [] } },
    );
    await openDialog();
    await fill("demo");
    await userEvent.click(create());
    expect(
      await screen.findByText("FAILED tests/test_math.py::test_add"),
    ).toBeVisible();
    expect(screen.getByText("The test command failed")).toBeVisible();
    expect(screen.getByText("Rolled back")).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Fix" }));
    expect(
      screen.queryByRole("region", { name: "Creating the project" }),
    ).toBeNull();
    expect(screen.getByLabelText("test")).toBeEnabled();
    expect(screen.getByLabelText("test")).toHaveFocus();
  });

  it("names what a rollback left behind", async () => {
    jobReply = job("failed", [["passed"], ["failed", { field: "template" }]], {
      rollback: { removed: [], left: ["/home/me/code/demo"] },
    });
    await openDialog();
    await fill("demo");
    await userEvent.click(create());
    expect(
      await screen.findByText("Left behind: /home/me/code/demo"),
    ).toBeVisible();
  });

  it("asks before Cancel stops the job", async () => {
    await openDialog();
    await fill("demo");
    await userEvent.click(create());
    await screen.findByRole("region", { name: "Creating the project" });
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    const confirm = screen.getByRole("dialog", {
      name: "Stop and remove what was created?",
    });
    expect(POST).not.toHaveBeenCalledWith(
      "/api/jobs/{job_id}/cancel",
      expect.anything(),
    );
    await userEvent.click(
      within(confirm).getByRole("button", { name: "Stop and remove" }),
    );
    expect(POST).toHaveBeenCalledWith("/api/jobs/{job_id}/cancel", {
      params: { path: { job_id: JOB_ID } },
    });
    expect(screen.queryByRole("dialog", { name: "New project" })).toBeNull();
  });

  it("shows a toast when a cancel's rollback leaves paths behind", async () => {
    POST.mockImplementation((path) => {
      if (path === "/api/jobs/{job_id}/cancel") {
        return ok(
          job("cancelled", [["passed"], ["failed"]], {
            rollback: { removed: [], left: ["/home/me/code/demo"] },
          }),
        );
      }
      return ok({ job_id: JOB_ID });
    });
    await openDialog();
    await fill("demo");
    await userEvent.click(create());
    await screen.findByRole("region", { name: "Creating the project" });
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    await userEvent.click(
      screen.getByRole("button", { name: "Stop and remove" }),
    );
    expect(
      await screen.findByText("Couldn't clean up demo · see Needs you on Home"),
    ).toBeVisible();
  });

  it("opens the panel on Spec with a toast on success", async () => {
    jobReply = job("succeeded", [
      ["passed"],
      ["passed"],
      ["passed"],
      ["passed"],
    ]);
    await openDialog();
    await fill("demo");
    await userEvent.click(create());
    expect(await screen.findByText("Panel at /p/demo?tab=spec")).toBeVisible();
    expect(screen.getByText(CREATED_TOAST).parentElement).toHaveAttribute(
      "aria-live",
      "polite",
    );
  });

  it("stops polling when the dialog closes", async () => {
    await openDialog();
    await fill("demo");
    await userEvent.click(create());
    await waitFor(
      () => {
        expect(jobPolls()).toBeGreaterThanOrEqual(2);
      },
      { timeout: 2000 },
    );
    await userEvent.click(screen.getByRole("button", { name: "Close" }));
    await userEvent.click(
      screen.getByRole("button", { name: "Stop and remove" }),
    );
    const polls = jobPolls();
    await new Promise((resolve) => setTimeout(resolve, 1200));
    expect(jobPolls()).toBe(polls);
  });

  it("offers Retry when the templates don't load", async () => {
    let fail = true;
    const usual = GET.getMockImplementation();
    GET.mockImplementation((path, init) =>
      path === "/api/templates" && fail
        ? Promise.reject(new Error("down"))
        : usual?.(path, init),
    );
    renderButton();
    await userEvent.click(screen.getByRole("button", { name: "New project" }));
    expect(
      await screen.findByText("Couldn't load the templates"),
    ).toBeVisible();
    fail = false;
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("fastapi-react")).toBeVisible();
  });
});

type Inspection = Schemas["RepoInspectionView"];

const INSPECTION: Inspection = {
  branch: "main",
  clean: true,
  dirty: [],
  origin: "https://github.com/me/demo",
  commands: {
    install: "just install",
    lint: null,
    test: "just test",
    source: "justfile",
  },
  agent_settings: [],
  notes_missing: [],
};

describe("New project from an existing repo", () => {
  let inspection: Inspection;
  let graphify: boolean;

  beforeEach(() => {
    vi.clearAllMocks();
    inspection = INSPECTION;
    graphify = true;
    vi.mocked(pickFolder).mockResolvedValue("/home/me/code/demo");
    GET.mockImplementation((path) => {
      if (path === "/api/templates") {
        return ok([TEMPLATE]);
      }
      if (path === "/api/settings") {
        return ok({ projects_dir: "/home/me/spoolhq-projects" });
      }
      if (path === "/api/agents") {
        return ok({
          backends: [],
          graphify: { installed: graphify, version: null, tested: null },
          fake_runner: null,
        });
      }
      if (path === "/api/jobs/{job_id}") {
        return ok(
          job("running", [["passed"], ["passed"], ["running"], ["pending"]], {
            source: "existing",
          }),
        );
      }
      throw new Error(`unexpected GET ${path}`);
    });
    POST.mockImplementation((path) => {
      if (path === "/api/repos/inspect") {
        return ok(inspection);
      }
      if (path === "/api/projects") {
        return ok({ job_id: JOB_ID });
      }
      throw new Error(`unexpected POST ${path}`);
    });
  });

  async function pick() {
    await openDialog();
    await userEvent.click(screen.getByRole("radio", { name: "Existing repo" }));
    await userEvent.type(screen.getByLabelText("Project name"), "demo");
    await userEvent.click(screen.getByRole("button", { name: "Choose…" }));
    await waitFor(() => {
      expect(POST).toHaveBeenCalledWith("/api/repos/inspect", {
        body: { path: "/home/me/code/demo" },
      });
    });
  }

  it("pre-fills the detected commands and says where they came from", async () => {
    await pick();
    expect(await screen.findByText(/Detected from justfile\./)).toBeVisible();
    expect(screen.getByLabelText("install")).toHaveValue("just install");
    expect(screen.getByLabelText("test")).toHaveValue("just test");
    expect(screen.getByLabelText("lint")).toHaveValue("");
    expect(screen.getByLabelText("lint")).toHaveAttribute(
      "placeholder",
      "e.g. just lint",
    );
    expect(screen.getByText("Clean · on main")).toBeVisible();
  });

  it("pre-fills a GitHub origin as the remote", async () => {
    await pick();
    await userEvent.click(screen.getByText("More"));
    await waitFor(() => {
      expect(screen.getByLabelText(/GitHub remote/)).toHaveValue(
        "https://github.com/me/demo",
      );
    });
    expect(screen.getByText("Detected from origin")).toBeVisible();
  });

  it("says the repo's own agent settings are ignored", async () => {
    inspection = {
      ...INSPECTION,
      agent_settings: [".claude/settings.json", ".mcp.json"],
    };
    await pick();
    expect(
      await screen.findByText(
        "This repo has its own agent settings (.claude/settings.json, .mcp.json). SpoolHQ ignores them during runs.",
      ),
    ).toBeVisible();
  });

  it("recommends Graphify only when it isn't installed", async () => {
    const line =
      "Recommended for existing repos: install Graphify so the agent can find its way around.";
    await pick();
    await screen.findByText("Clean · on main");
    expect(screen.queryByText(line)).toBeNull();
    cleanup();
    graphify = false;
    await pick();
    expect(await screen.findByText(line)).toBeVisible();
  });

  it("lists a dirty repo's files and keeps Create disabled", async () => {
    inspection = {
      ...INSPECTION,
      clean: false,
      dirty: [" M src/app.py", "?? notes.txt"],
    };
    await pick();
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(DIRTY_REASON);
    expect(alert).toHaveTextContent("M src/app.py");
    expect(alert).toHaveTextContent("?? notes.txt");
    await userEvent.type(screen.getByLabelText("lint"), "just lint");
    expect(create()).toBeDisabled();
  });

  it("shows the checks help on the existing repo's checklist", async () => {
    await pick();
    await screen.findByText(/Detected from justfile\./);
    await userEvent.type(screen.getByLabelText("lint"), "just lint");
    await userEvent.click(create());
    expect(await screen.findByText(CHECKS_HELP)).toBeVisible();
  });
});
