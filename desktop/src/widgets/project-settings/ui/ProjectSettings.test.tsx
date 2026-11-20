import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api, DaemonError } from "@/shared/api";

import { ProjectSettings } from "./ProjectSettings";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return { ...actual, api: { GET: vi.fn(), PUT: vi.fn() } };
});

type Handler = (path: string, init?: unknown) => unknown;
const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;
const PUT = vi.mocked(api.PUT) as unknown as ReturnType<typeof vi.fn<Handler>>;

const withEtag = (data: unknown, etag: string) =>
  Promise.resolve({
    data,
    response: new Response(null, { headers: { ETag: etag } }),
  });

const READY = { installed: true, logged_in: true, reason: null };
let backends: unknown[];
let settings: Record<string, unknown>;
let failSettings: DaemonError | null;

function apiError(status: number, extra: Partial<Record<string, unknown>>) {
  return new DaemonError({
    kind: "api",
    status,
    code: status === 412 ? "edit_conflict" : "validation_error",
    message: "",
    field: null,
    etag: null,
    current: null,
    ...extra,
  });
}

function show(onDirtyChange = vi.fn()) {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <ProjectSettings project="demo" onDirtyChange={onDirtyChange} />
    </QueryClientProvider>,
  );
  return onDirtyChange;
}

const sentBody = (call = 0) =>
  (PUT.mock.calls[call]?.[1] as { body: { settings: Record<string, unknown> } })
    .body.settings;
const sentEtag = (call = 0) =>
  (PUT.mock.calls[call]?.[1] as { params: { header: { "if-match": string } } })
    .params.header["if-match"];

describe("Settings tab · Agents", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    backends = [
      { name: "claude-code-cli", ...READY },
      {
        name: "codex-cli",
        installed: false,
        logged_in: false,
        reason: "codex: command not found",
      },
    ];
    settings = {
      name: "demo",
      agents: { default: "claude-code-cli", budget_per_ticket: { usd: 5 } },
    };
    failSettings = null;
    GET.mockImplementation((path) => {
      if (path === "/api/agents") {
        return Promise.resolve({
          data: { backends, graphify: { installed: false, version: null } },
        });
      }
      if (path === "/api/projects/{name}/settings") {
        return failSettings
          ? Promise.reject(failSettings)
          : withEtag({ settings }, '"e1"');
      }
      throw new Error(`unexpected GET ${path}`);
    });
  });

  it("renders the default and each role, with Use default first", async () => {
    show();
    expect(await screen.findByLabelText("Default backend")).toHaveValue(
      "claude-code-cli",
    );
    for (const role of ["Planner", "Implementer", "Reviewer"]) {
      const select = screen.getByLabelText(`${role} backend`);
      expect(select).toHaveValue("");
      expect(within(select).getAllByRole("option")[0]).toHaveTextContent(
        "Use default (Claude Code)",
      );
      expect(screen.getByLabelText(`${role} model`)).toHaveValue("");
    }
    expect(
      screen.getByText(/Other project settings come in a later version/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });

  it("marks a backend that isn't installed, with its reason as a tooltip", async () => {
    show();
    const reviewer = await screen.findByLabelText("Reviewer backend");
    expect(
      within(reviewer).getByRole("option", { name: "Codex (not installed)" }),
    ).toBeInTheDocument();
    await userEvent.selectOptions(reviewer, "codex-cli");
    expect(screen.getByText("Codex: Not installed")).toBeInTheDocument();
    expect(screen.getByRole("tooltip")).toHaveTextContent(
      "codex: command not found",
    );
  });

  it("saves only the changed keys with If-Match", async () => {
    PUT.mockImplementation((_path, init) =>
      withEtag((init as { body: unknown }).body, '"e2"'),
    );
    const dirty = show();
    await userEvent.selectOptions(
      await screen.findByLabelText("Reviewer backend"),
      "codex-cli",
    );
    await userEvent.type(screen.getByLabelText("Reviewer model"), "gpt-5");
    expect(dirty).toHaveBeenLastCalledWith(true);
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => {
      expect(dirty).toHaveBeenLastCalledWith(false);
    });
    expect(sentEtag()).toBe('"e1"');
    expect(sentBody()).toEqual({
      name: "demo",
      agents: {
        default: "claude-code-cli",
        budget_per_ticket: { usd: 5 },
        reviewer: { backend: "codex-cli", model: "gpt-5" },
      },
    });
    expect(screen.getByText("Saved")).toBeInTheDocument();
  });

  it("sends a mapping only for roles with a model", async () => {
    PUT.mockImplementation((_path, init) =>
      withEtag((init as { body: unknown }).body, '"e2"'),
    );
    show();
    await userEvent.type(
      await screen.findByLabelText("Planner model"),
      "claude-opus-x",
    );
    await userEvent.selectOptions(
      screen.getByLabelText("Implementer backend"),
      "codex-cli",
    );
    await userEvent.click(screen.getByText("Advanced"));
    await userEvent.type(
      screen.getByLabelText("Claude Code default model"),
      "claude-haiku-x",
    );
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => {
      expect(PUT).toHaveBeenCalled();
    });
    expect(sentBody().agents).toEqual({
      default: "claude-code-cli",
      budget_per_ticket: { usd: 5 },
      planner: { model: "claude-opus-x" },
      implementer: "codex-cli",
      backends: { "claude-code-cli": { model: "claude-haiku-x" } },
    });
  });

  it("shows each role's own model from the file, and keeps an untouched mapping", async () => {
    settings = {
      name: "demo",
      agents: { planner: { backend: "default", model: "big" } },
    };
    PUT.mockImplementation((_path, init) =>
      withEtag((init as { body: unknown }).body, '"e2"'),
    );
    show();
    expect(await screen.findByLabelText("Planner model")).toHaveValue("big");
    expect(screen.getByLabelText("Planner backend")).toHaveValue("");
    await userEvent.type(screen.getByLabelText("Reviewer model"), "small");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => {
      expect(PUT).toHaveBeenCalled();
    });
    expect(sentBody().agents).toEqual({
      planner: { backend: "default", model: "big" },
      reviewer: { model: "small" },
    });
  });

  it("Use default removes the role's key", async () => {
    settings = { name: "demo", agents: { planner: "codex-cli" } };
    PUT.mockImplementation((_path, init) =>
      withEtag((init as { body: unknown }).body, '"e2"'),
    );
    show();
    const planner = await screen.findByLabelText("Planner backend");
    expect(planner).toHaveValue("codex-cli");
    await userEvent.selectOptions(planner, "");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => {
      expect(PUT).toHaveBeenCalled();
    });
    expect(sentBody()).toEqual({ name: "demo", agents: {} });
  });

  it("shows the conflict bar on 412; Keep mine saves over the disk version", async () => {
    const disk = { name: "demo", default_branch: "trunk" };
    PUT.mockRejectedValueOnce(
      apiError(412, { etag: '"disk"', current: { settings: disk } }),
    ).mockImplementation((_path, init) =>
      withEtag((init as { body: unknown }).body, '"e3"'),
    );
    show();
    await userEvent.selectOptions(
      await screen.findByLabelText("Reviewer backend"),
      "codex-cli",
    );
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    const bar = await screen.findByRole("alert");
    expect(bar).toHaveTextContent("project.yaml changed on disk");
    await userEvent.click(
      within(bar).getByRole("button", { name: "Keep mine" }),
    );
    await waitFor(() => {
      expect(PUT).toHaveBeenCalledTimes(2);
    });
    expect(sentEtag(1)).toBe('"disk"');
    expect(sentBody(1)).toEqual({
      ...disk,
      agents: { reviewer: "codex-cli" },
    });
  });

  it("Reload takes the disk version and drops the edits", async () => {
    PUT.mockRejectedValueOnce(
      apiError(412, {
        etag: '"disk"',
        current: {
          settings: { name: "demo", agents: { reviewer: "codex-cli" } },
        },
      }),
    );
    show();
    await userEvent.type(await screen.findByLabelText("Planner model"), "opus");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    await userEvent.click(
      within(await screen.findByRole("alert")).getByRole("button", {
        name: "Reload",
      }),
    );
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByLabelText("Reviewer backend")).toHaveValue("codex-cli");
    expect(screen.getByLabelText("Planner model")).toHaveValue("");
  });

  it("puts a role model's 422 next to that role's model", async () => {
    PUT.mockRejectedValueOnce(
      apiError(422, {
        field: "agents.implementer.model",
        message:
          "project.yaml: agents.implementer.model: must be 1 to 100 characters from A-Z a-z 0-9 . _ : / @ - and not start with -",
      }),
    );
    show();
    const model = await screen.findByLabelText("Implementer model");
    await userEvent.type(model, "-rf");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => {
      expect(model).toHaveAttribute("aria-invalid", "true");
    });
    expect(model).toHaveAccessibleDescription(
      "must be 1 to 100 characters from A-Z a-z 0-9 . _ : / @ - and not start with -",
    );
    expect(screen.getByLabelText("Planner model")).toHaveAttribute(
      "aria-invalid",
      "false",
    );
  });

  it("puts a 422 next to its field", async () => {
    PUT.mockRejectedValueOnce(
      apiError(422, {
        field: "agents.backends.claude-code-cli.base_url",
        message:
          "project.yaml: agents.backends.claude-code-cli.base_url: 'http://example.com': plain http is allowed only for localhost; use https",
      }),
    );
    show();
    await userEvent.click(await screen.findByText("Advanced"));
    const url = screen.getByLabelText("Claude Code base URL");
    await userEvent.type(url, "http://example.com");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => {
      expect(url).toHaveAttribute("aria-invalid", "true");
    });
    expect(url).toHaveAccessibleDescription(
      "'http://example.com': plain http is allowed only for localhost; use https",
    );
  });

  it("shows loading, then an error with Retry", async () => {
    failSettings = apiError(422, { message: "project.yaml: name: bad" });
    show();
    expect(screen.getByText("Loading project.yaml…")).toBeInTheDocument();
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Couldn't load project.yaml");
    failSettings = null;
    await userEvent.click(within(alert).getByRole("button", { name: "Retry" }));
    expect(await screen.findByLabelText("Default backend")).toBeInTheDocument();
  });

  it("with no detected backends, points to App settings", async () => {
    backends = [];
    show();
    expect(
      await screen.findByText("No coding agents found"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Open App settings" }),
    ).toBeInTheDocument();
  });
});
