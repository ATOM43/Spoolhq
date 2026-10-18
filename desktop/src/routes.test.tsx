import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { invoke } from "@tauri-apps/api/core";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter } from "react-router";
import { RouterProvider } from "react-router/dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { routes } from "./routes";

vi.mock("@tauri-apps/api/core", () => ({ invoke: vi.fn() }));

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
    const body =
      path === "/api/health" ? '{"status":"ok"}' : '{"version":"0.0.0"}';
    return Promise.resolve({ status: 200, body });
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
      screen.getByRole("heading", { name: "Project demo" }),
    ).toBeInTheDocument();
    expect(screen.getByText("No spec yet")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("tab", { name: "Tickets" }));
    expect(screen.getByText("No tickets yet")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("tab", { name: "Run" }));
    expect(screen.getByText("Nothing running")).toBeInTheDocument();
  });
});
