import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { invoke } from "@tauri-apps/api/core";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter } from "react-router";
import { RouterProvider } from "react-router/dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { routes } from "./routes";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: vi.fn(),
  Channel: class {
    onmessage: unknown = null;
  },
}));

const invokeMock = vi.mocked(invoke);

function renderAt(path: string) {
  const queryClient = new QueryClient();
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

const BODIES: Record<string, string> = {
  "/api/health": '{"status":"ok"}',
  "/api/projects": "[]",
  "/api/agents": JSON.stringify({
    backends: [
      {
        name: "claude-code-cli",
        installed: true,
        version: "2.1.0",
        logged_in: true,
        auth_method: "subscription",
        billing: "subscription",
        policy_enforceable: true,
        reason: null,
        policy_parts: {},
        usable: true,
      },
    ],
    graphify: { installed: false, version: null, tested: false },
  }),
  "/api/settings": JSON.stringify({
    host: "127.0.0.1",
    port: 8765,
    log_level: "info",
    projects_dir: "/p",
    worktrees_dir: "/w",
    allowed_origins: [],
    secrets: {
      anthropic: { set: false, source: null },
      github: { set: false, source: null },
      clickup: { set: false, source: null },
    },
  }),
  "/api/projects/demo": JSON.stringify({
    name: "demo",
    done: 0,
    total: 0,
    run_state: "idle",
    needs_you: 0,
    latest_seq: 0,
    repo: "/code/demo",
    default_branch: "main",
    remote: null,
    invalid_tickets: 0,
    next_ticket: null,
    idle: null,
    remaining_h: 0,
  }),
  "/api/projects/demo/runs/current": JSON.stringify({
    project: "demo",
    active: false,
    working: false,
    run: null,
    attempts: 0,
    input_tokens: 0,
    output_tokens: 0,
    cost_micro_usd: null,
    phases: [],
    last_merged: null,
    latest_seq: 0,
  }),
  "/api/projects/demo/spec": '{"content":""}',
  "/api/projects/demo/tickets": '{"tickets":[],"invalid":[]}',
  "/api/projects/demo/plan": JSON.stringify({
    state: "none",
    generated_at: null,
    ticket_count: 0,
    total_h: 0,
    problems: [],
  }),
};

function daemonRunning() {
  invokeMock.mockImplementation((command, args) => {
    if (command === "daemon_info") {
      return Promise.resolve({
        port: 8765,
        token_present: true,
        token_path: "/t",
      });
    }
    const path = (args as { path: string }).path;
    const body = BODIES[path] ?? '{"version":"0.0.0"}';
    return Promise.resolve({ status: 200, body, etag: '"e1"' });
  });
}

function daemonStopped() {
  invokeMock.mockImplementation((command) => {
    if (command === "daemon_info") {
      return Promise.resolve({
        port: 8765,
        token_present: true,
        token_path: "/t",
      });
    }
    // Tauri rejects with the serialised Rust error, a plain object, not an Error.
    // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors
    return Promise.reject({
      kind: "not_running",
      port: 8765,
      message: "connection refused",
    });
  });
}

describe("app shell", () => {
  beforeEach(() => {
    invokeMock.mockReset();
  });

  it("shows Daemon ok when the daemon answers", async () => {
    daemonRunning();
    renderAt("/");
    expect(await screen.findByText("No projects yet")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Daemon ok · v0.0.0");
  });

  it("explains how to start a stopped daemon instead of a blank window", async () => {
    daemonStopped();
    renderAt("/");
    expect(
      await screen.findByRole("heading", { name: "The daemon isn't running" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Daemon not running");
    expect(screen.getByText("spool serve")).toBeInTheDocument();
  });

  it("opens the Settings dialog from Home", async () => {
    daemonRunning();
    renderAt("/");
    await userEvent.click(screen.getByRole("button", { name: "Settings" }));
    expect(screen.getByRole("dialog", { name: "Settings" })).toBeVisible();
  });

  it("shows the project panel with Spec, Tickets and Run tabs", async () => {
    daemonRunning();
    renderAt("/p/demo");
    expect(
      await screen.findByRole("heading", { name: "demo" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("tab", { name: "Spec", selected: true }),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("tab", { name: "Tickets 0" }));
    expect(
      await screen.findByText(
        "Write a spec first; the planner turns it into tickets.",
      ),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("tab", { name: "Run" }));
    expect(screen.getByText("Coming in T22")).toBeInTheDocument();
  });
});
