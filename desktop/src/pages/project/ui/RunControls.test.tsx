import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ProjectDetail } from "@/entities/project";
import type { CurrentRun } from "@/entities/run";
import { api } from "@/shared/api";

import { formatUsage, panelState } from "../model/state";
import { RunControls } from "./RunControls";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return { ...actual, api: { POST: vi.fn() } };
});

type Handler = (path: string, init?: unknown) => unknown;
const POST = vi.mocked(api.POST) as unknown as ReturnType<
  typeof vi.fn<Handler>
>;

function project(extra: Partial<ProjectDetail> = {}): ProjectDetail {
  return {
    name: "demo",
    done: 0,
    total: 3,
    run_state: "idle",
    needs_you: 0,
    latest_seq: 0,
    repo: "/code/demo",
    default_branch: "main",
    remote: null,
    invalid_tickets: 0,
    next_ticket: null,
    idle: null,
    remaining_h: 3,
    ...extra,
  };
}

type Run = NonNullable<CurrentRun["run"]>;

function current(run: Partial<Run> | null, active = true): CurrentRun {
  return {
    project: "demo",
    active,
    working: active,
    run:
      run === null
        ? null
        : {
            id: 1,
            kind: "ticket",
            ticket_id: "T15",
            status: "running",
            reason: null,
            started_at: "2026-11-01T12:00:00Z",
            ended_at: null,
            reset_at: null,
            progress_note: null,
            ...run,
          },
    attempts: 2,
    input_tokens: 80_000,
    output_tokens: 4_000,
    cost_micro_usd: null,
    phases: [{ id: 3, text: "Gates" }],
    last_merged: null,
    latest_seq: 3,
  };
}

function show(
  detail: ProjectDetail,
  run: CurrentRun | undefined,
  specEmpty = false,
) {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <RunControls
        project="demo"
        state={panelState(detail, run, specEmpty)}
        usage={formatUsage(run)}
        offline={null}
      />
    </QueryClientProvider>,
  );
}

const button = (name: RegExp | string) => screen.getByRole("button", { name });

function expectDisabled(reason: string) {
  for (const name of [/^Run next/, "Run all"]) {
    expect(button(name)).toBeDisabled();
    expect(button(name)).toHaveAccessibleDescription(reason);
  }
}

describe("run controls", () => {
  beforeEach(() => {
    POST.mockReset();
    POST.mockResolvedValue({ data: {}, response: new Response() });
  });

  it("no spec: Write a spec first", () => {
    show(project({ total: 0 }), current(null, false), true);
    expectDisabled("Write a spec first");
  });

  it("spec but no plan: Generate a plan first", () => {
    show(project({ total: 0 }), current(null, false));
    expectDisabled("Generate a plan first");
  });

  it("planning: Planner is running", () => {
    show(
      project({ total: 0 }),
      current({ kind: "plan", ticket_id: "plan" }, false),
    );
    expectDisabled("Planner is running");
  });

  it("draft plan: Approve the plan first", () => {
    show(
      project({
        idle: { code: "plan_not_approved", ticket_ids: ["T01"], message: "" },
      }),
      current(null, false),
    );
    expectDisabled("Approve the plan first");
  });

  it("approved and idle: Run next names the ticket and starts it", async () => {
    show(project({ next_ticket: "T11" }), current(null, false));
    expect(button("Run all")).toBeEnabled();
    await userEvent.click(button("Run next (T11)"));
    expect(POST).toHaveBeenCalledWith("/api/projects/{name}/run/next", {
      params: { path: { name: "demo" } },
    });
  });

  it("running: shows the step, Pause, and Cancel through a confirm", async () => {
    show(project({ run_state: "running" }), current({}));
    expect(
      screen.getByText("Running T15 · Gates · attempt 2"),
    ).toBeInTheDocument();
    expect(button("Pause")).toBeEnabled();
    expect(screen.queryByRole("button", { name: /^Run next/ })).toBeNull();
    await userEvent.click(button("Cancel"));
    const dialog = screen.getByRole("dialog", { name: "Cancel T15?" });
    expect(dialog).toHaveTextContent(
      "The worktree is removed and the ticket returns to Ready. Used so far: 84k tokens.",
    );
    expect(POST).not.toHaveBeenCalled();
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Cancel run" }),
    );
    expect(POST).toHaveBeenCalledWith("/api/projects/{name}/run/cancel", {
      params: { path: { name: "demo" } },
    });
  });

  it("paused by the user: Resume and Cancel", () => {
    show(project({ run_state: "paused" }), current({ status: "paused" }));
    expect(button("Resume")).toBeEnabled();
    expect(button("Cancel")).toBeEnabled();
  });

  it("paused by a usage limit: says when it resumes, offers Cancel only", () => {
    const reset = "2026-11-01T14:30:00";
    const at = new Date(reset).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    show(
      project({ run_state: "paused" }),
      current({ status: "paused", reset_at: reset }),
    );
    expect(
      screen.getByText(`Paused · usage limit · resumes ${at}`),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Resume" })).toBeNull();
    expect(button("Cancel")).toBeEnabled();
  });

  it("nothing ready: names the blocked ticket", () => {
    show(
      project({
        idle: {
          code: "blocked",
          ticket_ids: ["T09"],
          message: "T09 is blocked",
        },
      }),
      current(null, false),
    );
    expectDisabled("T09 is blocked — open it to unblock");
  });

  it("a run already going elsewhere: says so", () => {
    show(
      project({ idle: { code: "running", ticket_ids: ["T04"], message: "" } }),
      current(null, false),
    );
    expectDisabled("A run is already going");
  });

  it("all done: All tickets done", () => {
    show(
      project({
        done: 3,
        idle: { code: "all_done", ticket_ids: [], message: "" },
      }),
      current(null, false),
    );
    expectDisabled("All tickets done");
  });

  it("shows cost in USD for an API backend", () => {
    const run = current({});
    run.cost_micro_usd = 840_000;
    expect(formatUsage(run)).toBe("$0.84");
  });
});

describe("the tab a project opens on", () => {
  it("follows the state table", () => {
    const idle = current(null, false);
    expect(panelState(project({ total: 0 }), idle, true).tab).toBe("spec");
    expect(panelState(project({ next_ticket: "T01" }), idle, false).tab).toBe(
      "tickets",
    );
    expect(panelState(project(), current({}), false).tab).toBe("run");
  });
});
