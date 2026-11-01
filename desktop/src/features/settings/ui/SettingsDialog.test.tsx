import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api, DaemonError, getVersion, type Schemas } from "@/shared/api";

import { SET_UP_FIRST, SettingsDialog } from "./SettingsDialog";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return {
    ...actual,
    api: { GET: vi.fn(), PUT: vi.fn(), DELETE: vi.fn() },
    getVersion: vi.fn(),
  };
});

type Handler = (path: string, init?: unknown) => unknown;
const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;
const PUT = vi.mocked(api.PUT) as unknown as ReturnType<typeof vi.fn<Handler>>;

type Backend = Schemas["BackendView"];
type Secret = Schemas["SecretView"];

const ok = (data: unknown) =>
  Promise.resolve({ data, response: new Response() });

function backend(name: string, extra: Partial<Backend> = {}): Backend {
  return {
    name,
    installed: true,
    version: "1.0.0",
    logged_in: true,
    auth_method: null,
    billing: "subscription",
    policy_enforceable: true,
    reason: null,
    policy_parts: {},
    usable: true,
    ...extra,
  };
}

let backends: Backend[] = [];
let secrets: Record<string, Secret> = {};

function settings() {
  return {
    host: "127.0.0.1",
    port: 8765,
    log_level: "info",
    projects_dir: "/home/me/spoolhq-projects",
    worktrees_dir: "/home/me/.spoolhq/worktrees",
    allowed_origins: [],
    secrets,
  };
}

const NOT_SET: Secret = { set: false, source: null };

function renderDialog(firstRun = false) {
  const client = new QueryClient();
  render(
    <QueryClientProvider client={client}>
      <SettingsDialog firstRun={firstRun} />
    </QueryClientProvider>,
  );
  return client;
}

async function openSettings() {
  await userEvent.click(screen.getByRole("button", { name: "Settings" }));
  return screen.getByRole("dialog", { name: "Settings" });
}

describe("Settings", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    backends = [];
    secrets = { anthropic: NOT_SET, github: NOT_SET, clickup: NOT_SET };
    GET.mockImplementation((path) => {
      if (path === "/api/agents") {
        return ok({
          backends,
          graphify: { installed: true, version: "0.9.92", tested: true },
        });
      }
      if (path === "/api/settings") {
        return ok(settings());
      }
      throw new Error(`unexpected GET ${path}`);
    });
    PUT.mockImplementation(() => ok(undefined));
    vi.mocked(getVersion).mockResolvedValue({ version: "0.3.0" });
  });

  it("shows a loading state", async () => {
    GET.mockReturnValue(new Promise(() => undefined));
    renderDialog();
    await openSettings();
    expect(screen.getByText("Looking for coding agents…")).toBeInTheDocument();
  });

  it("shows an error with Retry", async () => {
    GET.mockImplementation(() =>
      Promise.reject(new DaemonError({ kind: "unauthorized" })),
    );
    renderDialog();
    await openSettings();
    expect(
      await screen.findByText(/Couldn't list the agents/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeEnabled();
  });

  it("says when no agent is found", async () => {
    renderDialog();
    await openSettings();
    expect(
      await screen.findByText("No coding agents found"),
    ).toBeInTheDocument();
  });

  it("lists each backend's version and login status, and Graphify", async () => {
    backends = [
      backend("claude-code-cli", { version: "2.1.0" }),
      backend("codex-cli", { logged_in: false }),
      backend("claude-agent-sdk", { installed: false, logged_in: false }),
    ];
    renderDialog();
    const dialog = await openSettings();
    expect(await within(dialog).findByText("Claude Code")).toBeInTheDocument();
    expect(within(dialog).getByText("2.1.0")).toBeInTheDocument();
    expect(within(dialog).getByText("Logged in")).toBeInTheDocument();
    expect(
      within(dialog).getByText(/Not logged in — run `codex login`/),
    ).toBeInTheDocument();
    expect(within(dialog).getByText("Not installed")).toBeInTheDocument();
    expect(within(dialog).getByText(/found · 0.9.92/)).toBeInTheDocument();
  });

  it("saves a secret without keeping its value in the DOM or the cache", async () => {
    secrets.github = { set: true, source: "keychain" };
    const client = renderDialog();
    const dialog = await openSettings();
    await userEvent.click(
      within(dialog).getByRole("tab", { name: "Accounts" }),
    );
    expect(
      await within(dialog).findByText("Set (keychain)"),
    ).toBeInTheDocument();
    expect(within(dialog).getAllByText("Not set")).toHaveLength(2);

    const row = within(dialog)
      .getByText("Anthropic API key")
      .closest("li") as HTMLElement;
    await userEvent.click(within(row).getByRole("button", { name: "Set" }));
    const secret = "sk-ant-very-secret-value";
    await userEvent.type(
      within(row).getByLabelText("New Anthropic API key"),
      secret,
    );
    secrets = { ...secrets, anthropic: { set: true, source: "keychain" } };
    await userEvent.click(within(row).getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(within(row).getByText("Set (keychain)")).toBeInTheDocument();
    });
    expect(PUT).toHaveBeenCalledWith("/api/settings/secrets/{secret}", {
      params: { path: { secret: "anthropic" } },
      body: { value: secret },
    });
    expect(document.body.innerHTML).not.toContain(secret);
    expect(screen.queryByDisplayValue(secret)).toBeNull();
    const cached = JSON.stringify([
      client
        .getQueryCache()
        .getAll()
        .map((query) => query.state),
      client
        .getMutationCache()
        .getAll()
        .map((mutation) => mutation.state),
    ]);
    expect(cached).not.toContain(secret);
    expect(within(row).getByRole("button", { name: "Replace" })).toBeEnabled();
  });

  it("explains why an env secret can't be removed here", async () => {
    secrets.clickup = { set: true, source: "env" };
    renderDialog();
    const dialog = await openSettings();
    await userEvent.click(
      within(dialog).getByRole("tab", { name: "Accounts" }),
    );
    const remove = await within(dialog).findByRole("button", {
      name: "Remove",
    });
    expect(remove).toBeDisabled();
    expect(remove).toHaveAccessibleDescription(/environment variable/);
  });

  it("opens by itself on first run and can't be closed until a backend is ready", async () => {
    backends = [backend("claude-code-cli", { logged_in: false })];
    renderDialog(true);
    const dialog = await screen.findByRole("dialog", { name: "Settings" });
    expect(
      within(dialog).getByRole("tab", { name: "Agents", selected: true }),
    ).toBeInTheDocument();
    const close = within(dialog).getByRole("button", { name: "Close" });
    expect(close).toBeDisabled();
    expect(close).toHaveAccessibleDescription(SET_UP_FIRST);
    await userEvent.keyboard("{Escape}");
    expect(screen.getByRole("dialog", { name: "Settings" })).toBeVisible();
  });

  it("can be closed on first run once a CLI is logged in, with no API key", async () => {
    backends = [backend("claude-code-cli")];
    renderDialog(true);
    await screen.findByRole("button", { name: "Settings" });
    // Nothing to set up: it doesn't open by itself.
    await waitFor(() => {
      expect(GET).toHaveBeenCalledWith("/api/settings");
    });
    expect(screen.queryByRole("dialog")).toBeNull();
    const dialog = await openSettings();
    const close = within(dialog).getByRole("button", { name: "Close" });
    expect(close).toBeEnabled();
    await userEvent.click(close);
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("shows General and About from the daemon's settings", async () => {
    renderDialog();
    const dialog = await openSettings();
    await userEvent.click(within(dialog).getByRole("tab", { name: "General" }));
    expect(
      await within(dialog).findByText("/home/me/spoolhq-projects"),
    ).toBeInTheDocument();
    await userEvent.click(within(dialog).getByRole("tab", { name: "About" }));
    expect(await within(dialog).findByText("0.3.0")).toBeInTheDocument();
    expect(
      within(dialog).getByText(/Running on 127.0.0.1:8765/),
    ).toBeInTheDocument();
  });
});
