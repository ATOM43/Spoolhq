import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { api, type Schemas } from "@/shared/api";

import { TrackerLine } from "./TrackerLine";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return { ...actual, api: { GET: vi.fn(), POST: vi.fn() } };
});

type Handler = (path: string, init?: unknown) => unknown;
const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;
const POST = vi.mocked(api.POST) as unknown as ReturnType<
  typeof vi.fn<Handler>
>;

const ok = (data: unknown) =>
  Promise.resolve({ data, response: new Response() });

let view: Schemas["TrackerView"];

function tracker(
  extra: Partial<Schemas["TrackerView"]> = {},
): Schemas["TrackerView"] {
  return {
    kind: "clickup",
    state: "ok",
    pending: 0,
    last_error: null,
    last_synced_at: null,
    failed_at: null,
    ...extra,
  };
}

const trackerGets = () =>
  GET.mock.calls.filter(([path]) => path === "/api/projects/{name}/tracker")
    .length;

function renderLine() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <TrackerLine project="demo" />
    </QueryClientProvider>,
  );
}

describe("TrackerLine", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    view = tracker();
    GET.mockImplementation(() => ok(view));
    POST.mockImplementation(() => ok({ queued: 1 }));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows nothing without a tracker", async () => {
    view = tracker({ kind: null, state: "off" });
    const { container } = renderLine();
    await waitFor(() => {
      expect(trackerGets()).toBe(1);
    });
    expect(container).toBeEmptyDOMElement();
  });

  it("shows when it last synced, with the absolute time on hover", async () => {
    const at = new Date(Date.now() - 2 * 60_000).toISOString();
    view = tracker({ last_synced_at: at });
    const { container } = renderLine();
    const time = await screen.findByText("synced 2 min ago");
    expect(time.parentElement).toHaveTextContent("ClickUp · synced 2 min ago");
    expect(time).toHaveAttribute("title", new Date(at).toLocaleString());
    expect(container.querySelector(".lucide-cloud-check")).not.toBeNull();
  });

  it("shows syncing with the pending count, and Push now disabled with a reason", async () => {
    view = tracker({ state: "syncing", pending: 3 });
    const { container } = renderLine();
    expect(
      await screen.findByText("ClickUp · syncing · 3 pending"),
    ).toBeInTheDocument();
    expect(container.querySelector(".lucide-loader-circle")).not.toBeNull();
    const push = screen.getByRole("button", { name: /Push now/ });
    expect(push).toBeDisabled();
    expect(push).toHaveAccessibleDescription(
      "Syncing 3 change(s); push again once it's done",
    );
  });

  it("shows a failed sync in red with its error as plain text, and Retry", async () => {
    const error = '<img src=x onerror="window.pwned=1"> ClickUp answered 500';
    view = tracker({ state: "failed", last_error: error });
    const { container } = renderLine();
    const label = await screen.findByText("ClickUp · sync failed");
    expect(label).toHaveClass("text-danger");
    expect(container.querySelector(".lucide-cloud-alert")).not.toBeNull();
    expect(screen.getByRole("tooltip")).toHaveTextContent(error);
    expect(label).toHaveAccessibleDescription(error);
    expect(container.querySelector("img")).toBeNull();
    expect((window as { pwned?: number }).pwned).toBeUndefined();
    expect(screen.getByRole("button", { name: "Retry" })).toBeEnabled();
  });

  it("Retry and Push now call their routes, then refetch the state", async () => {
    view = tracker({ state: "failed", last_error: "ClickUp answered 500" });
    renderLine();
    await userEvent.click(await screen.findByRole("button", { name: "Retry" }));
    expect(POST).toHaveBeenCalledWith("/api/projects/{name}/tracker/retry", {
      params: { path: { name: "demo" } },
    });
    await waitFor(() => {
      expect(trackerGets()).toBe(2);
    });

    view = tracker();
    await userEvent.click(screen.getByRole("button", { name: /Push now/ }));
    expect(POST).toHaveBeenCalledWith("/api/projects/{name}/tracker/push", {
      params: { path: { name: "demo" } },
    });
    await waitFor(() => {
      expect(trackerGets()).toBe(3);
    });
    expect(screen.queryByRole("button", { name: "Retry" })).toBeNull();
  });

  it("polls every 15 s while shown, and stops once it leaves the screen", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const { unmount } = renderLine();
    await screen.findByText(/ClickUp/);
    expect(trackerGets()).toBe(1);
    await act(() => vi.advanceTimersByTimeAsync(15_000));
    expect(trackerGets()).toBe(2);
    unmount();
    await act(() => vi.advanceTimersByTimeAsync(60_000));
    expect(trackerGets()).toBe(2);
  });

  it("doesn't poll a project without a tracker", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    view = tracker({ kind: null, state: "off" });
    renderLine();
    await waitFor(() => {
      expect(trackerGets()).toBe(1);
    });
    await act(() => vi.advanceTimersByTimeAsync(60_000));
    expect(trackerGets()).toBe(1);
  });
});
