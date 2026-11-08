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
    api: { GET: vi.fn(), PUT: vi.fn(), POST: vi.fn(), DELETE: vi.fn() },
    getVersion: vi.fn(),
  };
});

type Handler = (path: string, init?: unknown) => unknown;
const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;
const PUT = vi.mocked(api.PUT) as unknown as ReturnType<typeof vi.fn<Handler>>;
const POST = vi.mocked(api.POST) as unknown as ReturnType<
  typeof vi.fn<Handler>
>;

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
let fakeRunner: string | null = null;
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
    fakeRunner = null;
    secrets = { anthropic: NOT_SET, github: NOT_SET, clickup: NOT_SET };
    GET.mockImplementation((path) => {
      if (path === "/api/agents") {
        return ok({
          backends,
          graphify: { installed: true, version: "0.9.92", tested: true },
          fake_runner: fakeRunner,
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
    const field = within(row).getByLabelText(/Anthropic API key/);
    const secret = "sk-ant-very-secret-value";
    await userEvent.type(field, secret);
    secrets = { ...secrets, anthropic: { set: true, source: "keychain" } };
    await userEvent.click(within(row).getByRole("button", { name: "Save" }));
    expect(field).toHaveValue("");

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
    expect(within(row).getByRole("button", { name: "Test" })).toBeEnabled();
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
    for (const name of ["Close", "Done"]) {
      const button = within(dialog).getByRole("button", { name });
      expect(button).toBeDisabled();
      expect(button).toHaveAccessibleDescription(SET_UP_FIRST);
    }
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
    const done = within(dialog).getByRole("button", { name: "Done" });
    expect(done).toBeEnabled();
    await userEvent.click(done);
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

  it("has underlined tabs, a ✕ and a footer with Done", async () => {
    backends = [backend("claude-code-cli")];
    renderDialog();
    const dialog = await openSettings();
    expect(
      within(dialog)
        .getAllByRole("tab")
        .map((tab) => tab.textContent),
    ).toEqual(["Agents", "Accounts", "General", "About"]);
    expect(
      within(dialog).getByText("You can change these any time from Settings"),
    ).toBeInTheDocument();
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Close" }),
    );
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("shows the Agent SDK without a key as neutral, with the raw message under Details", async () => {
    backends = [
      backend("claude-code-cli"),
      backend("codex-cli", { logged_in: false }),
      backend("claude-agent-sdk", {
        logged_in: false,
        reason: "ANTHROPIC_API_KEY is not set",
      }),
    ];
    renderDialog();
    const dialog = await openSettings();
    const sdk = await within(dialog).findByText("Needs an API key (optional)");
    expect(sdk).toHaveClass("text-ink-muted");
    expect(sdk).not.toHaveClass("text-warning");
    // A CLI that isn't logged in isn't a warning while another backend is ready.
    expect(within(dialog).getByText(/Not logged in/)).not.toHaveClass(
      "text-warning",
    );
    const details = within(dialog)
      .getByText("Details")
      .closest("details") as HTMLDetailsElement;
    expect(details.open).toBe(false);
    expect(details).toHaveTextContent("ANTHROPIC_API_KEY is not set");
  });

  it("warns in amber only when no backend is ready", async () => {
    backends = [backend("claude-code-cli", { logged_in: false })];
    renderDialog();
    const dialog = await openSettings();
    expect(await within(dialog).findByText(/Not logged in/)).toHaveClass(
      "text-warning",
    );
    expect(within(dialog).getByRole("status")).toHaveTextContent(SET_UP_FIRST);
  });

  it("shows the dev fake runner first, in amber, and doesn't block", async () => {
    backends = [backend("claude-code-cli", { logged_in: false })];
    fakeRunner = "gate-retry";
    renderDialog();
    const dialog = await openSettings();
    const line = await within(dialog).findByText(
      "Fake runner (dev): gate-retry",
    );
    expect(line).toHaveClass("text-warning");
    expect(within(dialog).getAllByRole("status")).toEqual([line]);
    expect(within(dialog).getByText(/Not logged in/)).not.toHaveClass(
      "text-warning",
    );
  });

  it("can't test a secret that isn't set", async () => {
    renderDialog();
    const dialog = await openSettings();
    await userEvent.click(
      within(dialog).getByRole("tab", { name: "Accounts" }),
    );
    const row = (await within(dialog).findByText("GitHub token")).closest(
      "li",
    ) as HTMLElement;
    const test = within(row).getByRole("button", { name: "Test" });
    expect(test).toBeDisabled();
    expect(test).toHaveAccessibleDescription("Save a value first");
  });

  it.each([
    [
      { ok: true, message: "Key works" },
      "Key works · tested just now",
      "lucide-circle-check",
    ],
    [
      { ok: false, message: "Rejected (401)" },
      "Rejected (401)",
      "lucide-octagon-x",
    ],
    [
      { ok: false, message: "Rejected (403)" },
      "Rejected (403)",
      "lucide-octagon-x",
    ],
    [{ ok: false, message: "Timed out" }, "Timed out", "lucide-octagon-x"],
    [
      { ok: false, message: "Couldn't reach GitHub" },
      "Couldn't reach GitHub",
      "lucide-octagon-x",
    ],
    [
      { ok: false, message: "Unexpected response (500)" },
      "Unexpected response (500)",
      "lucide-octagon-x",
    ],
  ])("shows a test result with its icon: %j", async (result, text, icon) => {
    secrets.github = { set: true, source: "keychain" };
    POST.mockImplementation(() => ok(result));
    renderDialog();
    const dialog = await openSettings();
    await userEvent.click(
      within(dialog).getByRole("tab", { name: "Accounts" }),
    );
    const row = (await within(dialog).findByText("GitHub token")).closest(
      "li",
    ) as HTMLElement;
    await userEvent.click(within(row).getByRole("button", { name: "Test" }));
    const shown = await within(row).findByRole("status");
    expect(shown).toHaveTextContent(text);
    expect(shown.querySelector("svg")).toHaveClass(icon);
    expect(POST).toHaveBeenCalledWith("/api/settings/secrets/{secret}/test", {
      params: { path: { secret: "github" } },
    });

    // Not kept: closing the dialog drops it.
    await userEvent.click(within(dialog).getByRole("button", { name: "Done" }));
    await openSettings();
    await userEvent.click(screen.getByRole("tab", { name: "Accounts" }));
    await screen.findByText("GitHub token");
    expect(screen.queryByText(text)).toBeNull();
  });
});
