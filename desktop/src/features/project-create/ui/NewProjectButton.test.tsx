import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api, DaemonError, pickFolder } from "@/shared/api";

import { NewProjectButton } from "./NewProjectButton";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return {
    ...actual,
    api: { GET: vi.fn(), POST: vi.fn(), PUT: vi.fn() },
    pickFolder: vi.fn(),
  };
});

type Handler = (path: string, init?: unknown) => unknown;
const mocked = (fn: unknown) => fn as ReturnType<typeof vi.fn<Handler>>;
const GET = mocked(api.GET);
const POST = mocked(api.POST);
const PUT = mocked(api.PUT);

const ok = (data: unknown, headers: Record<string, string> = {}) =>
  Promise.resolve({ data, response: new Response(null, { headers }) });

function apiError(field: string | null, message: string, status = 422) {
  return new DaemonError({
    kind: "api",
    status,
    code: status === 422 ? "validation_error" : "conflict",
    message,
    field,
    etag: null,
    current: null,
  });
}

const TEMPLATES = [
  { name: "fastapi-react", description: "FastAPI and React." },
  { name: "cli-tool", description: "A Python CLI." },
];
const SETTINGS = {
  name: "demo",
  commands: { install: "just install", lint: "just lint", test: "just test" },
};

function result(status: string, extra: Record<string, unknown> = {}) {
  return {
    status,
    exit_code: status === "passed" ? 0 : 1,
    duration_s: 1.25,
    output: "",
    output_truncated: false,
    timeout_s: 90,
    ...extra,
  };
}

function renderButton() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <NewProjectButton />
    </QueryClientProvider>,
  );
}

async function openDialog() {
  renderButton();
  await userEvent.click(screen.getByRole("button", { name: "New project" }));
  return screen.getByRole("dialog", { name: "New project" });
}

async function createDemo() {
  const dialog = await openDialog();
  await userEvent.type(within(dialog).getByLabelText("Name"), "demo");
  await userEvent.type(
    within(dialog).getByLabelText("Repository folder"),
    "/repos/demo",
  );
  await userEvent.click(
    within(dialog).getByRole("button", { name: "Create project" }),
  );
  return screen.findByRole("dialog", { name: "Stack commands" });
}

describe("New project", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    GET.mockImplementation((path) => {
      if (path === "/api/templates") {
        return ok(TEMPLATES);
      }
      if (path === "/api/projects/{name}/settings") {
        return ok({ settings: SETTINGS }, { ETag: '"etag-1"' });
      }
      throw new Error(`unexpected GET ${path}`);
    });
    POST.mockImplementation((path) =>
      path === "/api/projects"
        ? ok({ name: "demo", path: "/w/demo", missing_notes: [] })
        : Promise.reject(new Error(`unexpected POST ${path}`)),
    );
  });

  it("says what is missing before Create is enabled", async () => {
    const dialog = await openDialog();
    const create = within(dialog).getByRole("button", {
      name: "Create project",
    });
    expect(create).toBeDisabled();
    expect(within(dialog).getByText("Enter a name.")).toBeInTheDocument();
    await userEvent.type(within(dialog).getByLabelText("Name"), "demo");
    expect(within(dialog).getByText("Choose a folder.")).toBeInTheDocument();
  });

  it("fills the repository from the folder picker and creates the project", async () => {
    vi.mocked(pickFolder).mockResolvedValue("/home/me/repo");
    const dialog = await openDialog();
    await userEvent.type(within(dialog).getByLabelText("Name"), "demo");
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Choose…" }),
    );
    expect(within(dialog).getByLabelText("Repository folder")).toHaveValue(
      "/home/me/repo",
    );
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Create project" }),
    );
    await screen.findByRole("dialog", { name: "Stack commands" });
    expect(POST).toHaveBeenCalledWith("/api/projects", {
      body: { name: "demo", repo: "/home/me/repo", branch: "main" },
    });
  });

  it("creates from a template chosen from the daemon's list", async () => {
    const dialog = await openDialog();
    await userEvent.type(within(dialog).getByLabelText("Name"), "demo");
    await userEvent.click(within(dialog).getByLabelText(/A template/));
    const select = within(dialog).getByLabelText("Template");
    await waitFor(() => {
      expect(select).toBeEnabled();
    });
    await userEvent.selectOptions(select, "fastapi-react");
    expect(within(dialog).getByText("FastAPI and React.")).toBeInTheDocument();
    await userEvent.type(
      within(dialog).getByLabelText("New or empty folder"),
      "/repos/new",
    );
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Create project" }),
    );
    await screen.findByRole("dialog", { name: "Stack commands" });
    expect(POST).toHaveBeenCalledWith("/api/projects", {
      body: {
        name: "demo",
        repo: "/repos/new",
        branch: "main",
        template: "fastapi-react",
      },
    });
  });

  it("shows API field errors next to their fields", async () => {
    POST.mockRejectedValueOnce(
      apiError("name", "name: String should match pattern"),
    );
    const dialog = await openDialog();
    await userEvent.type(within(dialog).getByLabelText("Name"), "Bad Name");
    await userEvent.type(
      within(dialog).getByLabelText("Repository folder"),
      "/r",
    );
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Create project" }),
    );
    const name = within(dialog).getByLabelText("Name");
    await waitFor(() => {
      expect(name).toHaveAccessibleDescription(
        "name: String should match pattern",
      );
    });
    expect(name).toHaveAttribute("aria-invalid", "true");

    POST.mockRejectedValueOnce(apiError("repo", "repo: not a git repository"));
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Create project" }),
    );
    await waitFor(() => {
      expect(
        within(dialog).getByLabelText("Repository folder"),
      ).toHaveAccessibleDescription("repo: not a git repository");
    });

    POST.mockRejectedValueOnce(
      apiError(null, "project folder already exists: /w/demo", 409),
    );
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Create project" }),
    );
    expect(
      await within(dialog).findByText("project folder already exists: /w/demo"),
    ).toBeInTheDocument();
  });

  it("tests each stack command and shows pass and fail", async () => {
    POST.mockImplementation((path, init) => {
      if (path === "/api/projects") {
        return ok({ name: "demo", path: "/w/demo", missing_notes: [] });
      }
      const { gate } = (init as { body: { gate: string } }).body;
      return gate === "lint"
        ? ok(result("passed", { output: "All checks passed!" }))
        : ok(result("failed", { output: "FAILED tests/test_a.py::test_x" }));
    });
    const dialog = await createDemo();
    expect(within(dialog).getByLabelText("Lint")).toHaveValue("just lint");

    await userEvent.click(
      within(dialog).getByRole("button", { name: "Test Lint" }),
    );
    expect(
      await within(dialog).findByText(/Passed · 1\.3 s/),
    ).toBeInTheDocument();
    expect(within(dialog).getByText("All checks passed!")).toBeInTheDocument();

    await userEvent.click(
      within(dialog).getByRole("button", { name: "Test Test" }),
    );
    expect(
      await within(dialog).findByText(/Failed \(exit 1\)/),
    ).toBeInTheDocument();
    expect(
      within(dialog).getByText("FAILED tests/test_a.py::test_x"),
    ).toBeInTheDocument();
    expect(POST).toHaveBeenCalledWith("/api/projects/{name}/commands/test", {
      params: { path: { name: "demo" } },
      body: { gate: "test", command: "just test" },
    });
  });

  it("shows a refused command under its field and a timeout", async () => {
    POST.mockImplementation((path, init) => {
      if (path === "/api/projects") {
        return ok({ name: "demo", path: "/w/demo", missing_notes: [] });
      }
      const { gate } = (init as { body: { gate: string } }).body;
      return gate === "install"
        ? Promise.reject(
            apiError("command", "command: shell syntax isn't supported"),
          )
        : ok(result("timed_out", { exit_code: null }));
    });
    const dialog = await createDemo();
    const install = within(dialog).getByLabelText("Install");
    await userEvent.clear(install);
    await userEvent.type(install, "make && make install");
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Test Install" }),
    );
    await waitFor(() => {
      expect(install).toHaveAccessibleDescription(
        "command: shell syntax isn't supported",
      );
    });
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Test Lint" }),
    );
    expect(
      await within(dialog).findByText(/Timed out after 90 s/),
    ).toBeInTheDocument();
  });

  it("saves the commands with the ETag and closes", async () => {
    PUT.mockReturnValue(ok({ settings: SETTINGS }));
    const dialog = await createDemo();
    const lint = within(dialog).getByLabelText("Lint");
    await userEvent.clear(lint);
    await userEvent.type(lint, "uv run ruff check");
    expect(
      within(dialog).getByRole("button", { name: "Test Lint" }),
    ).toBeEnabled();
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Save commands" }),
    );
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull();
    });
    expect(PUT).toHaveBeenCalledWith("/api/projects/{name}/settings", {
      params: { path: { name: "demo" }, header: { "if-match": '"etag-1"' } },
      body: {
        settings: {
          ...SETTINGS,
          commands: {
            install: "just install",
            lint: "uv run ruff check",
            test: "just test",
          },
        },
      },
    });
  });

  it("disables Test and Save for an empty command and says why", async () => {
    const dialog = await createDemo();
    await userEvent.clear(within(dialog).getByLabelText("Test"));
    expect(
      within(dialog).getByRole("button", { name: "Test Test" }),
    ).toBeDisabled();
    expect(
      within(dialog).getByText("Enter a command to test it."),
    ).toBeInTheDocument();
    expect(
      within(dialog).getByRole("button", { name: "Save commands" }),
    ).toBeDisabled();
    expect(
      within(dialog).getByText("Enter the test command to save."),
    ).toBeInTheDocument();
  });
});
