import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter } from "react-router";
import { RouterProvider } from "react-router/dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ProjectDetail } from "@/entities/project";
import type { Ticket } from "@/entities/ticket";
import {
  api,
  DaemonError,
  getDaemonInfo,
  getHealth,
  getVersion,
  subscribeEvents,
} from "@/shared/api";

import { ProjectPage } from "./ProjectPage";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return {
    ...actual,
    api: { GET: vi.fn(), POST: vi.fn(), PUT: vi.fn() },
    subscribeEvents: vi.fn(),
    getDaemonInfo: vi.fn(),
    getHealth: vi.fn(),
    getVersion: vi.fn(),
  };
});

type Handler = (path: string, init?: unknown) => unknown;
const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;
const ok = (data: unknown) =>
  Promise.resolve({ data, response: new Response() });

const T01: Ticket = {
  id: "T01",
  file_name: "T01-repo.md",
  meta: {
    id: "T01",
    title: "Repository and tooling",
    phase: 0,
    depends_on: [],
    status: "done",
    estimate_h: 1.5,
    review_required: false,
  },
  body: "## Scope\n\n- CI on three systems\n\n## Done when\n\n- [ ] CI is green\n",
  activity: null,
};

const T04: Ticket = {
  id: "T04",
  file_name: "T04-db.md",
  meta: {
    id: "T04",
    title: "Database layer",
    phase: 1,
    depends_on: ["T01"],
    status: "blocked",
    estimate_h: 2,
    review_required: true,
  },
  body: [
    "## Purpose",
    "Store results.",
    "",
    "## Scope",
    "- [x] tables",
    "- <script>window.pwned = true</script>",
    "",
    "## Done when",
    "- [ ] Migrations run",
    "- [ ] Rollback works",
    "- [ ] `just test` passes",
    "",
  ].join("\n"),
  activity: {
    attempts: 2,
    tokens: 10,
    cost_micro_usd: null,
    run_id: 7,
    reason: "gates failed",
  },
};

const T05: Ticket = {
  ...T01,
  id: "T05",
  file_name: "T05-api.md",
  meta: {
    ...T01.meta,
    id: "T05",
    title: "API",
    status: "ready",
    depends_on: ["T04"],
  },
};

const DETAIL: ProjectDetail = {
  name: "demo",
  done: 1,
  total: 3,
  run_state: "idle",
  needs_you: 1,
  latest_seq: 0,
  draft: 0,
  remaining_h: 4,
  has_spec: true,
  repo: "/code/demo",
  default_branch: "main",
  remote: null,
  invalid_tickets: 0,
  next_ticket: null,
  idle: null,
};

const T04_RUN = {
  id: 7,
  kind: "ticket",
  ticket_id: "T04",
  status: "blocked",
  reason: "gates failed after 2 retries",
  started_at: "2026-11-06T10:00:00Z",
  ended_at: null,
  reset_at: null,
  progress_note: null,
};
const T04_ATTEMPT = {
  number: 2,
  run_id: 7,
  kind: "gate_retry",
  status: "gates_failed",
  backend: "claude-code-cli",
  model: null,
  input_tokens: 1000,
  output_tokens: 500,
  cost_micro_usd: null,
  started_at: "2026-11-06T10:00:00Z",
  ended_at: "2026-11-06T10:22:05Z",
};

const detailOf = (ticket: Ticket) => ({
  ...ticket,
  run: ticket.id === "T04" ? T04_RUN : null,
  attempts: ticket.id === "T04" ? [T04_ATTEMPT] : [],
  git: {
    branch: null,
    commits: null,
    diff_lines: null,
    commit: null,
    commit_url: null,
    tag: null,
    pr_number: null,
    pr_url: null,
    pr_state: null,
    pr_checked_at: null,
  },
});

const notFound = () =>
  Promise.reject(
    new DaemonError({
      kind: "api",
      status: 404,
      code: "not_found",
      message: "no review",
      field: null,
      etag: null,
      current: null,
    }),
  );

function show(path: string) {
  const router = createMemoryRouter(
    [{ path: "/p/:id", element: <ProjectPage /> }],
    { initialEntries: [path] },
  );
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return router;
}

const drawer = () => screen.queryByRole("complementary");

describe("ticket drawer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getDaemonInfo).mockResolvedValue({
      port: 8765,
      tokenPresent: true,
      tokenPath: "/t",
    });
    vi.mocked(getHealth).mockResolvedValue({ status: "ok" });
    vi.mocked(getVersion).mockResolvedValue({ version: "0.0.0" });
    vi.mocked(subscribeEvents).mockReturnValue(() => undefined);
    GET.mockImplementation((path, init) => {
      switch (path) {
        case "/api/projects/{name}":
          return ok(DETAIL);
        case "/api/projects/{name}/spec":
          return ok({ content: "# Objective" });
        case "/api/projects/{name}/runs/current":
          return ok({ active: false, run: null, phases: [], attempts: 0 });
        case "/api/projects/{name}/tickets":
          return ok({ tickets: [T01, T04, T05], invalid: [] });
        case "/api/projects/{name}/plan":
          return ok({
            state: "approved",
            generated_at: null,
            ticket_count: 3,
            total_h: 5.5,
            problems: [],
          });
        case "/api/projects/{name}/runs/{run_id}":
          return ok({ attempts: [{ number: 3 }, { number: 4 }] });
        case "/api/projects/{name}/runs/{run_id}/attempts/{number}/review": {
          const { number } = (init as { params: { path: { number: number } } })
            .params.path;
          // The newest attempt stopped before review; the one before has items.
          return number === 4
            ? notFound()
            : ok({
                verdict: "changes_requested",
                summary: "",
                stopped: null,
                items: [
                  { text: "Migrations run", met: true, reason: "ok" },
                  {
                    text: "Rollback works",
                    met: false,
                    reason: "no down step",
                  },
                ],
              });
        }
        case "/api/projects/{name}/tickets/{ticket_id}": {
          const { ticket_id } = (
            init as { params: { path: { ticket_id: string } } }
          ).params.path;
          const ticket = [T01, T04, T05].find((t) => t.id === ticket_id);
          return ticket ? ok(detailOf(ticket)) : notFound();
        }
        case "/api/agents":
          return ok({ backends: [], graphify: { installed: false } });
        case "/api/settings":
          return ok({ secrets: {} });
      }
      throw new Error(`unexpected GET ${path}`);
    });
  });

  it("opens from a row click with ?ticket=, and Esc closes it", async () => {
    const router = show("/p/demo?tab=tickets");
    await userEvent.click(await screen.findByText("Database layer"));

    expect(router.state.location.search).toBe("?tab=tickets&ticket=T04");
    const aside = within(drawer() as HTMLElement);
    expect(
      aside.getByRole("heading", { name: "Database layer" }),
    ).toBeVisible();
    expect(aside.getByText("Blocked")).toBeInTheDocument();
    expect(
      await aside.findByRole("button", { name: "Unblock" }),
    ).toBeInTheDocument();

    await userEvent.keyboard("{Escape}");
    expect(drawer()).toBeNull();
    expect(router.state.location.search).toBe("?tab=tickets");
  });

  it("opens from a problem link", async () => {
    GET.mockImplementation(
      ((original) => (path: string, init?: unknown) =>
        path === "/api/projects/{name}/plan"
          ? ok({
              state: "draft",
              generated_at: null,
              ticket_count: 1,
              total_h: 2,
              problems: [
                {
                  code: "missing_done_when",
                  message: "T05 has no 'Done when'",
                  ticket_ids: ["T05"],
                },
              ],
            })
          : original(path, init))(GET.getMockImplementation() as Handler),
    );
    const router = show("/p/demo?tab=tickets");
    await userEvent.click(
      await screen.findByRole("button", { name: "T05 has no 'Done when'" }),
    );
    expect(router.state.location.search).toBe("?tab=tickets&ticket=T05");
    expect(
      within(drawer() as HTMLElement).getByRole("heading", { name: "API" }),
    ).toBeInTheDocument();
  });

  it("is restored from the URL on reload, with its sections", async () => {
    show("/p/demo?tab=tickets&ticket=T04");
    const aside = within(
      await screen.findByRole("complementary", { name: "Ticket T04" }),
    );
    expect(
      await aside.findByRole("heading", { name: "Database layer" }),
    ).toBeInTheDocument();
    // Scope: markdown without the Done-when section; raw HTML stays inert.
    const scope = within(aside.getByRole("region", { name: "Scope" }));
    expect(scope.getByText("Store results.")).toBeInTheDocument();
    expect(scope.getByRole("checkbox")).toBeDisabled();
    expect(scope.queryByText("Migrations run")).toBeNull();
    expect(document.querySelector("script")).toBeNull();

    const done = aside.getByRole("region", { name: "Done when" });
    const items = await vi.waitFor(() => {
      const found = [...done.querySelectorAll("li")].map((li) =>
        li.getAttribute("data-review"),
      );
      expect(found).toEqual(["met", "not_met", "none"]);
      return found;
    });
    expect(items).toHaveLength(3);
    expect(within(done).getByText("Not reviewed yet")).toBeInTheDocument();
    expect(within(done).getByText("no down step")).toBeInTheDocument();

    const deps = within(aside.getByRole("region", { name: "Dependencies" }));
    expect(deps.getByRole("button", { name: "Open T01" })).toHaveAttribute(
      "data-met",
      "true",
    );
    expect(deps.getByRole("button", { name: "Open T05" })).toBeInTheDocument();
    const details = within(aside.getByRole("region", { name: "Details" }));
    expect(details.getByText("Yes")).toBeInTheDocument();
  });

  it("follows a dependency chip, and ✕ closes", async () => {
    const router = show("/p/demo?tab=tickets&ticket=T04");
    const aside = within(
      await screen.findByRole("complementary", { name: "Ticket T04" }),
    );
    const deps = within(
      await aside.findByRole("region", { name: "Dependencies" }),
    );
    await userEvent.click(deps.getByRole("button", { name: "Open T01" }));
    expect(router.state.location.search).toBe("?tab=tickets&ticket=T01");
    await userEvent.click(
      within(drawer() as HTMLElement).getByRole("button", { name: "Close" }),
    );
    expect(drawer()).toBeNull();
  });

  it("follows a Waits-for chip, and an attempt link opens the Run tab", async () => {
    const router = show("/p/demo?tab=tickets&ticket=T05");
    const aside = within(
      await screen.findByRole("complementary", { name: "Ticket T05" }),
    );
    // T05 waits for T04 (blocked): its action says so.
    expect(
      await aside.findByRole("button", { name: "Run this ticket" }),
    ).toBeDisabled();
    // The "Waits for" chip in the header (the Dependencies section has one too).
    await userEvent.click(
      aside.getAllByRole("button", { name: "Open T04" })[0] as HTMLElement,
    );
    expect(router.state.location.search).toBe("?tab=tickets&ticket=T04");
    const blocked = within(drawer() as HTMLElement);
    await userEvent.click(
      await blocked.findByRole("button", {
        name: "Open attempt 2 in the Run tab",
      }),
    );
    expect(router.state.location.search).toBe(
      "?tab=tickets&ticket=T04&attempt=2",
    );
    expect(screen.getByRole("tab", { name: /Run/ })).toHaveAttribute(
      "data-state",
      "active",
    );
  });

  it("says when the ticket no longer exists", async () => {
    const router = show("/p/demo?tab=tickets&ticket=T99");
    expect(
      await screen.findByText("This ticket no longer exists."),
    ).toBeInTheDocument();
    const aside = within(drawer() as HTMLElement);
    await userEvent.click(
      aside.getAllByRole("button", { name: "Close" }).at(-1) as HTMLElement,
    );
    expect(drawer()).toBeNull();
    expect(router.state.location.search).toBe("?tab=tickets");
  });
});
