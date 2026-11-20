import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api, DaemonError } from "@/shared/api";
import { Toaster } from "@/shared/ui";

import { NewTicketDrawer } from "./NewTicketDrawer";

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
const apiError = (status: number, message: string, field: string | null) =>
  new DaemonError({
    kind: "api",
    status,
    code: "x",
    message,
    field,
    etag: null,
    current: null,
  });

const SET_UP_FIRST =
  "Set up an agent first: log in to a coding CLI or add an API key";
const DRAFT_PATH = "/api/projects/{name}/tickets/draft/{job_id}";

interface Problem {
  code: string;
  message: string;
  field: string;
}
const draft = (ref: string, more: Record<string, unknown> = {}) => ({
  ref,
  title: `Part ${ref}`,
  scope: `- Scope of ${ref}`,
  done_when: ["It works", "`true` passes"],
  depends_on: [] as string[],
  estimate_h: 2,
  review_required: false,
  phase: 0,
  problems: [] as Problem[],
  ...more,
});

let state: {
  ready: boolean;
  idle: { code: string; message: string } | null;
  /** The job's state on each read; the last one repeats. */
  reads: { state: string; error?: string }[];
  drafts: ReturnType<typeof draft>[];
};

beforeEach(() => {
  vi.clearAllMocks();
  state = {
    ready: true,
    idle: null,
    reads: [{ state: "succeeded" }],
    drafts: [draft("D1")],
  };
  GET.mockImplementation((path) => {
    switch (path) {
      case "/api/projects/{name}":
        return ok({ name: "demo", idle: state.idle });
      case "/api/projects/{name}/tickets":
        return ok({
          tickets: [{ id: "T02", meta: { id: "T02", title: "Table" } }],
          invalid: [],
        });
      case "/api/agents":
        return ok({
          backends: state.ready ? [{ installed: true, logged_in: true }] : [],
        });
      case "/api/settings":
        return ok({ secrets: {} });
      case DRAFT_PATH: {
        const read =
          state.reads.length > 1 ? state.reads.shift() : state.reads[0];
        return ok({
          id: "j1",
          error: null,
          drafts: read?.state === "succeeded" ? state.drafts : [],
          ...read,
        });
      }
    }
    throw new Error(`unexpected GET ${path}`);
  });
  POST.mockImplementation((path) => {
    switch (path) {
      case "/api/projects/{name}/tickets/draft":
        return ok({ job_id: "j1" });
      case "/api/projects/{name}/tickets":
        return ok({ id: "T46" });
      case "/api/projects/{name}/tickets/batch":
        return ok({
          tickets: state.drafts.map((_, i) => ({ id: `T4${String(i + 6)}` })),
        });
    }
    return ok({});
  });
});

const onSaved = vi.fn<(id: string) => void>();
const onClose = vi.fn<() => void>();

function show() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <Toaster />
      <NewTicketDrawer project="demo" onSaved={onSaved} onClose={onClose} />
    </QueryClientProvider>,
  );
}

const draftButton = () =>
  screen.getByRole("button", { name: "Draft with planner" });
const describeBox = () => screen.getByRole("textbox", { name: "Describe it" });
const draftReads = () => GET.mock.calls.filter(([p]) => p === DRAFT_PATH);
const wait = (ms: number) => new Promise((done) => setTimeout(done, ms));

async function drawUp(request = "Add CSV export") {
  const view = show();
  await userEvent.type(describeBox(), request);
  await vi.waitFor(() => {
    expect(draftButton()).toBeEnabled();
  });
  await userEvent.click(draftButton());
  return view;
}

describe("Drafting in the Add ticket form", () => {
  it("disables Draft with planner with the daemon's reasons", async () => {
    state.ready = false;
    const view = show();
    await userEvent.type(describeBox(), "x");
    await vi.waitFor(() => {
      expect(draftButton()).toHaveAccessibleDescription(SET_UP_FIRST);
    });
    expect(draftButton()).toBeDisabled();
    expect(screen.getByRole("button", { name: "Open Settings" })).toBeVisible();
    view.unmount();

    state.ready = true;
    const message = "Set the stack commands in project.yaml first";
    state.idle = { code: "no_commands", message };
    show();
    await userEvent.type(describeBox(), "x");
    await vi.waitFor(() => {
      expect(draftButton()).toHaveAccessibleDescription(message);
    });
    expect(screen.queryByRole("button", { name: "Open Settings" })).toBeNull();
  });

  it("writing by hand works as before; the counter counts", async () => {
    show();
    expect(screen.getByText("0 / 2,000")).toBeInTheDocument();
    await userEvent.type(describeBox(), "abc");
    expect(screen.getByText("3 / 2,000")).toBeInTheDocument();
    await userEvent.type(screen.getByRole("textbox", { name: "Title" }), "T");
    // Typed by hand: no draft may overwrite it.
    expect(screen.queryByRole("textbox", { name: "Describe it" })).toBeNull();
  });

  it("shows a spinner while drafting, and Cancel calls the cancel route", async () => {
    state.reads = [{ state: "running" }];
    await drawUp();
    expect(POST).toHaveBeenCalledWith("/api/projects/{name}/tickets/draft", {
      params: { path: { name: "demo" } },
      body: { request: "Add CSV export" },
    });
    expect(await screen.findByRole("status")).toHaveTextContent("Drafting…");
    expect(draftButton()).toBeDisabled();
    expect(draftButton()).toHaveAccessibleDescription(
      "The planner is drafting already",
    );
    state.reads = [{ state: "cancelled" }];
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(POST).toHaveBeenCalledWith(
      "/api/projects/{name}/tickets/draft/{job_id}/cancel",
      { params: { path: { name: "demo", job_id: "j1" } } },
    );
    await vi.waitFor(() => {
      expect(screen.queryByRole("status")).toBeNull();
    });
    expect(describeBox()).toHaveValue("Add CSV export");
  });

  it("polls while the job runs and stops when it ends", async () => {
    state.reads = [
      { state: "running" },
      { state: "running" },
      { state: "succeeded" },
    ];
    await drawUp();
    await screen.findByText(
      "Drafted by the planner; check it before saving.",
      {},
      { timeout: 3000 },
    );
    const reads = draftReads().length;
    expect(reads).toBe(3);
    await wait(1200);
    expect(draftReads()).toHaveLength(reads);
  });

  it("closing while drafting asks, cancels, and stops polling", async () => {
    state.reads = [{ state: "running" }];
    const view = await drawUp();
    await screen.findByRole("status");
    await userEvent.keyboard("{Escape}");
    expect(onClose).not.toHaveBeenCalled();
    await userEvent.click(
      screen.getByRole("button", { name: "Stop drafting" }),
    );
    expect(POST).toHaveBeenCalledWith(
      "/api/projects/{name}/tickets/draft/{job_id}/cancel",
      { params: { path: { name: "demo", job_id: "j1" } } },
    );
    expect(onClose).toHaveBeenCalled();
    // The page then unmounts the drawer.
    view.unmount();
    const reads = draftReads().length;
    await wait(1200);
    expect(draftReads()).toHaveLength(reads);
  });

  it("one draft fills the form and saves through the single create", async () => {
    await drawUp();
    expect(
      await screen.findByText(
        "Drafted by the planner; check it before saving.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Title" })).toHaveValue(
      "Part D1",
    );
    expect(screen.getByRole("textbox", { name: "Done when" })).toHaveValue(
      "- [ ] It works\n- [ ] `true` passes",
    );
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(POST).toHaveBeenCalledWith("/api/projects/{name}/tickets", {
      params: { path: { name: "demo" } },
      body: {
        title: "Part D1",
        scope: "- Scope of D1",
        done_when: "- [ ] It works\n- [ ] `true` passes",
        depends_on: [],
        estimate_h: 2,
        review_required: false,
      },
    });
    await vi.waitFor(() => {
      expect(onSaved).toHaveBeenCalledWith("T46");
    });
  });

  it("three drafts show as tabs; removing D1 drops it from D2's dependencies", async () => {
    state.drafts = [
      draft("D1"),
      draft("D2", { depends_on: ["D1", "T02"] }),
      draft("D3"),
    ];
    await drawUp("split: add CSV export");
    expect(
      await screen.findByText("The planner split this into 3 tickets"),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("tab").map((t) => t.textContent)).toEqual([
      "D1",
      "D2",
      "D3",
    ]);
    await userEvent.click(screen.getByRole("tab", { name: "D2" }));
    expect(screen.getByRole("checkbox", { name: /D1/ })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /T02/ })).toBeChecked();

    await userEvent.click(screen.getByRole("button", { name: "Remove D1" }));
    await userEvent.click(screen.getByRole("button", { name: "Remove draft" }));
    expect(screen.getAllByRole("tab")).toHaveLength(2);
    expect(
      screen.getByText("The planner split this into 2 tickets"),
    ).toBeVisible();
    expect(
      screen.getByText("D1 was removed, so this no longer depends on it."),
    ).toBeVisible();
    expect(screen.queryByRole("checkbox", { name: /D1/ })).toBeNull();
    expect(screen.getByRole("checkbox", { name: /D3/ })).not.toBeChecked();
  });

  it("problems show by their field and tab, and Save all waits for them", async () => {
    state.drafts = [
      draft("D1"),
      draft("D2", {
        title: "",
        problems: [
          { code: "schema", message: "title: missing", field: "title" },
        ],
      }),
      draft("D3", {
        estimate_h: 6,
        problems: [
          {
            code: "estimate_too_high",
            message: "6 h is over 4 h; split it",
            field: "estimate_h",
          },
        ],
      }),
    ];
    await drawUp("split: add CSV export");
    const saveAll = await screen.findByRole("button", { name: "Save all" });
    expect(saveAll).toBeDisabled();
    expect(saveAll).toHaveAccessibleDescription("Fix 2 problems first");
    expect(screen.getByRole("tab", { name: "D2, 1 problem" })).toBeVisible();
    expect(screen.getByRole("tab", { name: "D1" })).toBeVisible();

    await userEvent.click(screen.getByRole("tab", { name: "D2, 1 problem" }));
    expect(screen.getByText("title: missing")).toBeVisible();
    await userEvent.type(
      screen.getByRole("textbox", { name: "Title" }),
      "Read rows",
    );
    expect(screen.queryByText("title: missing")).toBeNull();
    expect(screen.getByRole("tab", { name: "D2" })).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Save all" }),
    ).toHaveAccessibleDescription("Fix 1 problem first");

    await userEvent.click(screen.getByRole("tab", { name: "D3, 1 problem" }));
    expect(screen.getByText("6 h is over 4 h; split it")).toBeVisible();
    const estimate = screen.getByRole("spinbutton");
    await userEvent.clear(estimate);
    // Cleared by the edit: the form's own check applies to the empty field now.
    expect(screen.queryByText("6 h is over 4 h; split it")).toBeNull();
    expect(
      screen.getByText("Between 0.5 and 8 h, in steps of 0.5"),
    ).toBeVisible();
    await userEvent.type(estimate, "3");
    expect(screen.getByRole("button", { name: "Save all" })).toBeEnabled();
  });

  it("Save all saves through the batch route, then shows the first ticket", async () => {
    state.drafts = [draft("D1"), draft("D2", { depends_on: ["D1"] })];
    await drawUp("split: add CSV export");
    const ticketsReads = () =>
      GET.mock.calls.filter(([p]) => p === "/api/projects/{name}/tickets")
        .length;
    await userEvent.click(
      await screen.findByRole("button", { name: "Save all" }),
    );
    const before = ticketsReads();
    expect(POST).toHaveBeenCalledWith("/api/projects/{name}/tickets/batch", {
      params: { path: { name: "demo" } },
      body: {
        tickets: [
          expect.objectContaining({
            ref: "D1",
            title: "Part D1",
            depends_on: [],
            phase: 0,
          }),
          expect.objectContaining({
            ref: "D2",
            depends_on: ["D1"],
            done_when: "- [ ] It works\n- [ ] `true` passes",
            estimate_h: 2,
          }),
        ],
      },
    });
    expect(await screen.findByText("Added T46, T47")).toBeVisible();
    expect(onSaved).toHaveBeenCalledWith("T46");
    expect(ticketsReads()).toBeGreaterThanOrEqual(before);
  });

  it("a batch 422 lands on its tab and field", async () => {
    state.drafts = [draft("D1"), draft("D2", { depends_on: ["T02"] })];
    POST.mockImplementation((path) =>
      path === "/api/projects/{name}/tickets/batch"
        ? Promise.reject(
            apiError(422, "unknown dependency T02", "tickets.1.depends_on"),
          )
        : ok({ job_id: "j1" }),
    );
    await drawUp("split: add CSV export");
    await userEvent.click(
      await screen.findByRole("button", { name: "Save all" }),
    );
    expect(await screen.findByText("unknown dependency T02")).toBeVisible();
    expect(screen.getByRole("tab", { name: "D2, 1 problem" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    const deps = screen.getByRole("group", { name: "Depends on" });
    expect(within(deps).getByText("unknown dependency T02")).toBeVisible();
  });

  it("Discard keeps the Describe it text; closing with drafts asks first", async () => {
    await drawUp();
    await screen.findByText("Drafted by the planner; check it before saving.");
    await userEvent.keyboard("{Escape}");
    expect(onClose).not.toHaveBeenCalled();
    expect(
      screen.getByRole("dialog", { name: "Discard the new ticket?" }),
    ).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Keep going" }));

    await userEvent.click(screen.getByRole("button", { name: "Discard" }));
    expect(describeBox()).toHaveValue("Add CSV export");
    expect(screen.getByRole("textbox", { name: "Title" })).toHaveValue("");
  });

  it("a failed job shows its message, and Try again resends the text", async () => {
    state.reads = [
      { state: "failed", error: "The planner's answer couldn't be read" },
    ];
    await drawUp();
    expect(
      await screen.findByText("The planner's answer couldn't be read"),
    ).toBeVisible();
    state.reads = [{ state: "running" }];
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    const starts = POST.mock.calls.filter(
      ([p]) => p === "/api/projects/{name}/tickets/draft",
    );
    expect(starts).toHaveLength(2);
    expect(starts[1]?.[1]).toEqual({
      params: { path: { name: "demo" } },
      body: { request: "Add CSV export" },
    });
  });

  it("a draft's scope renders inert", async () => {
    const scope =
      '<script>window.hacked = 1</script>\n<img src="x" onerror="window.hacked = 1">\n[click](javascript:alert(1))';
    state.drafts = [draft("D1", { scope })];
    await drawUp();
    const view = document.body;
    expect(await screen.findByRole("textbox", { name: "Scope" })).toHaveValue(
      scope,
    );
    expect(view.querySelector("script, img")).toBeNull();
    expect(view.querySelector('a[href^="javascript"]')).toBeNull();
    expect((window as { hacked?: number }).hacked).toBeUndefined();
  });
});
