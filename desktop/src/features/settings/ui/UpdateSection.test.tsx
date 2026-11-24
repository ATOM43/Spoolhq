import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  api,
  getUpdateStatus,
  installUpdate,
  type UpdateStatus,
} from "@/shared/api";

import { UpdateSection } from "./UpdateSection";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return {
    ...actual,
    api: { GET: vi.fn() },
    getUpdateStatus: vi.fn(),
    installUpdate: vi.fn(),
  };
});

type Handler = (path: string) => unknown;
const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;

const NOTES =
  '<a href="https://evil.example">Click</a> <img src=x onerror="alert(1)">';
let projects: unknown[] = [];

function status(extra: Partial<UpdateStatus> = {}): UpdateStatus {
  return {
    current_version: "0.1.0",
    check: {
      state: "available",
      version: "0.2.0",
      notes: NOTES,
      minimum_version: null,
      checked_at: Date.now(),
    },
    install: "in_place",
    external_daemon: false,
    installing: false,
    install_error: null,
    ...extra,
  };
}

function renderSection(value: UpdateStatus) {
  vi.mocked(getUpdateStatus).mockResolvedValue(value);
  const { container } = render(
    <QueryClientProvider client={new QueryClient()}>
      <UpdateSection />
    </QueryClientProvider>,
  );
  return container;
}

describe("UpdateSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    projects = [];
    GET.mockImplementation(() =>
      Promise.resolve({ data: projects, response: new Response() }),
    );
  });

  it("says up to date with the time and Check now", async () => {
    renderSection(
      status({ check: { state: "up_to_date", checked_at: Date.now() } }),
    );
    expect(
      await screen.findByText(/SpoolHQ is up to date · checked/),
    ).toHaveTextContent("just now");
    await userEvent.click(screen.getByRole("button", { name: "Check now" }));
    expect(getUpdateStatus).toHaveBeenCalledWith(true);
  });

  it("shows a failed check as one quiet line, no alert", async () => {
    renderSection(
      status({ check: { state: "failed", checked_at: Date.now() } }),
    );
    expect(
      await screen.findByText(/Couldn't check for updates ·/),
    ).toBeInTheDocument();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("says when checks are off, without Check now", async () => {
    renderSection(status({ check: { state: "off" } }));
    expect(
      await screen.findByText("Update checks are off (General)."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("shows both versions and the notes as plain text, never HTML or links", async () => {
    const container = renderSection(status());
    expect(
      await screen.findByText("Update available · v0.1.0 → v0.2.0"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Release notes").textContent).toBe(NOTES);
    expect(container.querySelector("a, img")).toBeNull();
    expect(screen.queryByRole("link")).toBeNull();
  });

  it("installs and shows why an install stopped", async () => {
    vi.mocked(installUpdate).mockResolvedValue(
      status({
        install_error:
          "The update couldn't be verified; nothing was installed.",
      }),
    );
    renderSection(status());
    await userEvent.click(
      await screen.findByRole("button", { name: "Install and restart" }),
    );
    expect(installUpdate).toHaveBeenCalled();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The update couldn't be verified; nothing was installed.",
    );
  });

  it("disables Install and restart with the reason while a run is going", async () => {
    projects = [
      { name: "demo", run_state: "running", run: { ticket_id: "T05" } },
    ];
    renderSection(status());
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Install and restart" }),
      ).toBeDisabled();
    });
    expect(
      screen.getAllByText("Wait for the run to finish (T05)").length,
    ).toBeGreaterThan(0);
  });

  it("shows no install button for a .deb or .rpm install", async () => {
    renderSection(status({ install: "package" }));
    expect(
      await screen.findByText("Download the new package from the release page"),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Install and restart" }),
    ).toBeNull();
  });

  it("says an external daemon keeps running", async () => {
    renderSection(status({ external_daemon: true }));
    expect(
      await screen.findByText(
        "Your own daemon keeps running; restart it to update it.",
      ),
    ).toBeInTheDocument();
  });
});
