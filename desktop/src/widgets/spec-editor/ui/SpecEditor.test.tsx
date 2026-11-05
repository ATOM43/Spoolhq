import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ProjectDetail } from "@/entities/project";
import type { CurrentRun } from "@/entities/run";
import { api, DaemonError } from "@/shared/api";

import { AUTOSAVE_MS } from "../model/autosave";
import { SpecEditor } from "./SpecEditor";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return { ...actual, api: { GET: vi.fn(), PUT: vi.fn(), POST: vi.fn() } };
});

type Handler = (path: string, init?: unknown) => unknown;
const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;
const PUT = vi.mocked(api.PUT) as unknown as ReturnType<typeof vi.fn<Handler>>;
const POST = vi.mocked(api.POST) as unknown as ReturnType<
  typeof vi.fn<Handler>
>;

const withEtag = (data: unknown, etag: string) =>
  Promise.resolve({
    data,
    response: new Response(null, { headers: { ETag: etag } }),
  });

const PROJECT: ProjectDetail = {
  name: "demo",
  done: 0,
  total: 0,
  run_state: "idle",
  needs_you: 0,
  latest_seq: 0,
  draft: 0,
  has_spec: false,
  repo: "/code/demo",
  default_branch: "main",
  remote: null,
  invalid_tickets: 0,
  next_ticket: null,
  idle: null,
  remaining_h: 0,
};

// A logged-in CLI, so the agent check never blocks Generate plan here.
const READY_AGENTS = {
  backends: [{ name: "claude-code-cli", installed: true, logged_in: true }],
  graphify: { installed: false, version: null, tested: false },
};

function conflict(content: string, etag: string) {
  return new DaemonError({
    kind: "api",
    status: 412,
    code: "edit_conflict",
    message: "CONTEXT.md changed",
    field: null,
    etag,
    current: { content },
  });
}

function show(project: ProjectDetail = PROJECT, run?: CurrentRun) {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <SpecEditor project={project} run={run} onViewPlan={vi.fn()} />
    </QueryClientProvider>,
  );
}

const source = () => screen.findByLabelText("CONTEXT.md source");
const type = async (text: string) => {
  fireEvent.change(await source(), { target: { value: text } });
};
const afterAutosave = () =>
  new Promise((resolve) => setTimeout(resolve, AUTOSAVE_MS + 150));

describe("Spec tab", () => {
  let disk = "";
  beforeEach(() => {
    vi.clearAllMocks();
    disk = "# Objective\nShip it.";
    GET.mockImplementation((path) =>
      path === "/api/agents"
        ? withEtag(READY_AGENTS, "")
        : path === "/api/settings"
          ? withEtag({ secrets: {} }, "")
          : withEtag({ content: disk }, '"e1"'),
    );
    PUT.mockImplementation(() => withEtag({}, '"e2"'));
    POST.mockImplementation(() => withEtag({ run_id: 1 }, ""));
  });

  it("saves once with If-Match after typing stops", async () => {
    show();
    await type("# Objective\nShip");
    await type("# Objective\nShip it");
    await type("# Objective\nShip it now.");
    expect(screen.getByText("Unsaved changes")).toBeInTheDocument();
    await afterAutosave();
    await waitFor(() => {
      expect(screen.getByText("Saved")).toBeInTheDocument();
    });
    expect(PUT).toHaveBeenCalledTimes(1);
    expect(PUT).toHaveBeenCalledWith("/api/projects/{name}/spec", {
      params: { path: { name: "demo" }, header: { "if-match": '"e1"' } },
      body: { content: "# Objective\nShip it now." },
    });
  });

  it("saves now on Ctrl+S", async () => {
    show();
    await type("# Objective\nNow.");
    fireEvent.keyDown(await source(), { key: "s", ctrlKey: true });
    await waitFor(() => {
      expect(PUT).toHaveBeenCalledTimes(1);
    });
  });

  it("shows the conflict bar on 412 and overwrites only after Keep mine", async () => {
    PUT.mockImplementationOnce(() =>
      Promise.reject(conflict("someone else's", '"disk"')),
    );
    show();
    await type("mine");
    await afterAutosave();
    expect(
      await screen.findByText("CONTEXT.md changed on disk"),
    ).toBeInTheDocument();
    expect(screen.getByText("Conflict")).toBeInTheDocument();
    await afterAutosave();
    expect(PUT).toHaveBeenCalledTimes(1); // nothing more until a click
    expect(await source()).toHaveValue("mine");

    await userEvent.click(screen.getByRole("button", { name: "Keep mine" }));
    await waitFor(() => {
      expect(PUT).toHaveBeenCalledTimes(2);
    });
    expect(PUT).toHaveBeenLastCalledWith("/api/projects/{name}/spec", {
      params: { path: { name: "demo" }, header: { "if-match": '"disk"' } },
      body: { content: "mine" },
    });
    expect(await screen.findByText("Saved")).toBeInTheDocument();
    expect(screen.queryByText("CONTEXT.md changed on disk")).toBeNull();
  });

  it("Reload takes the disk version and saves nothing", async () => {
    PUT.mockImplementationOnce(() =>
      Promise.reject(conflict("the disk version", '"disk"')),
    );
    show();
    await type("mine");
    await afterAutosave();
    await userEvent.click(
      await screen.findByRole("button", { name: "Reload" }),
    );
    expect(await source()).toHaveValue("the disk version");
    expect(screen.getByText("Saved")).toBeInTheDocument();
    await afterAutosave();
    expect(PUT).toHaveBeenCalledTimes(1);
  });

  it("an empty spec shows the outline and Generate plan says why it's off", async () => {
    disk = "";
    show();
    expect(await source()).toHaveAttribute(
      "placeholder",
      expect.stringContaining("# Objective") as string,
    );
    expect(
      screen.getByText(
        "Paste an existing task description or start from this outline.",
      ),
    ).toBeInTheDocument();
    const generate = screen.getByRole("button", { name: "Generate plan" });
    expect(generate).toBeDisabled();
    expect(generate).toHaveAccessibleDescription(
      "Write at least an objective first",
    );
  });

  it("Generate plan starts the planner", async () => {
    show();
    await userEvent.click(
      await screen.findByRole("button", { name: "Generate plan" }),
    );
    expect(POST).toHaveBeenCalledWith("/api/projects/{name}/plan/generate", {
      params: { path: { name: "demo" } },
    });
  });

  it("shows the planner's failure with Retry", async () => {
    show(PROJECT, {
      project: "demo",
      active: false,
      working: false,
      run: {
        id: 2,
        kind: "plan",
        ticket_id: "plan",
        status: "blocked",
        reason: "the planner returned no tickets",
        started_at: "2026-11-01T12:00:00Z",
        ended_at: "2026-11-01T12:01:00Z",
        reset_at: null,
        progress_note: null,
      },
      attempts: 1,
      input_tokens: 0,
      output_tokens: 0,
      cost_micro_usd: null,
      phases: [],
      last_merged: null,
      latest_seq: 9,
    });
    expect(
      await screen.findByText(
        "Planning failed: the planner returned no tickets",
      ),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(POST).toHaveBeenCalledTimes(1);
  });

  it("becomes Re-plan once a plan exists, and is off while a draft waits", async () => {
    show({
      ...PROJECT,
      total: 2,
      idle: { code: "plan_not_approved", ticket_ids: ["T01"], message: "" },
    });
    const replan = await screen.findByRole("button", { name: "Re-plan" });
    expect(replan).toBeDisabled();
    expect(replan).toHaveAccessibleDescription(/A draft plan exists/);
  });

  it("asks before re-planning an approved plan", async () => {
    show({ ...PROJECT, total: 2, next_ticket: "T01" });
    await userEvent.click(
      await screen.findByRole("button", { name: "Re-plan" }),
    );
    expect(POST).not.toHaveBeenCalled();
    await userEvent.click(
      screen.getAllByRole("button", { name: "Re-plan" }).at(-1) as HTMLElement,
    );
    expect(POST).toHaveBeenCalledTimes(1);
  });

  it("renders the preview from the source, inertly", async () => {
    disk = "# Title\n\n<script>bad()</script>\n\n[x](javascript:alert(1))";
    show();
    const preview = await screen.findByRole("region", { name: "Preview" });
    expect(preview.querySelector("h1")).toHaveTextContent("Title");
    expect(preview.querySelector("script")).toBeNull();
    expect(preview.querySelector("a")?.getAttribute("href") ?? "").toBe("");
  });

  it("shows the word count next to the save state", async () => {
    show();
    expect(await screen.findByText("4 words")).toBeInTheDocument();
    await type("one");
    expect(screen.getByText("1 word")).toBeInTheDocument();
  });

  const importMd = async (text: string) => {
    const file = new File([text], "task.md", { type: "text/markdown" });
    await userEvent.upload(
      await screen.findByLabelText("Markdown file to import"),
      file,
    );
  };

  it("imports a .md into an empty spec without asking", async () => {
    disk = "";
    show();
    await importMd("# Imported\nText.");
    await waitFor(async () => {
      expect(await source()).toHaveValue("# Imported\nText.");
    });
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("asks before an import replaces a spec that isn't empty", async () => {
    show();
    await importMd("# Imported");
    await screen.findByRole("dialog", {
      name: "Replace the spec with task.md?",
    });
    expect(await source()).toHaveValue("# Objective\nShip it.");
    await userEvent.click(screen.getByRole("button", { name: "Keep going" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(await source()).toHaveValue("# Objective\nShip it.");

    await importMd("# Imported");
    await userEvent.click(
      await screen.findByRole("button", { name: "Replace spec" }),
    );
    expect(await source()).toHaveValue("# Imported");
    await afterAutosave();
    await waitFor(() => {
      expect(PUT).toHaveBeenCalledWith(
        "/api/projects/{name}/spec",
        expect.objectContaining({ body: { content: "# Imported" } }),
      );
    });
  });
});
