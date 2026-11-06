import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Plan } from "@/entities/plan";
import type { ProjectDetail } from "@/entities/project";
import type { Ticket, TicketStatus } from "@/entities/ticket";
import { api, DaemonError } from "@/shared/api";

import { TicketList } from "./TicketList";

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

function ticket(
  id: string,
  status: TicketStatus,
  extra: Partial<Ticket["meta"]> = {},
  activity: Ticket["activity"] = null,
): Ticket {
  return {
    id,
    file_name: `${id}-x.md`,
    meta: {
      id,
      title: `Title ${id}`,
      phase: 0,
      depends_on: [],
      status,
      estimate_h: 2,
      review_required: false,
      ...extra,
    },
    body: "## Done when\n\n- [ ] works\n",
    activity,
  };
}

const PLAN: Plan = {
  state: "approved",
  generated_at: "2026-11-06T10:00:00+00:00",
  ticket_count: 0,
  total_h: 0,
  problems: [],
};

let tickets: Ticket[];
let plan: Plan;

function project(extra: Partial<ProjectDetail> = {}): ProjectDetail {
  return {
    name: "demo",
    done: 0,
    total: tickets.length,
    run_state: "idle",
    needs_you: 0,
    latest_seq: 0,
    draft: 0,
    remaining_h: 0,
    has_spec: true,
    repo: "/code/demo",
    default_branch: "main",
    remote: null,
    invalid_tickets: 0,
    next_ticket: null,
    idle: null,
    ...extra,
  };
}

const onOpen = vi.fn<(id: string) => void>();
const onOpenSpec = vi.fn<() => void>();

function show(detail: ProjectDetail = project()) {
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <TicketList project={detail} onOpen={onOpen} onOpenSpec={onOpenSpec} />
    </QueryClientProvider>,
  );
}

const groups = () =>
  [...document.querySelectorAll("tbody[data-group]")].map((group) =>
    group.getAttribute("data-group"),
  );
const rows = () =>
  [...document.querySelectorAll("tr[data-ticket]")].map((row) =>
    row.getAttribute("data-ticket"),
  );

describe("Tickets tab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    tickets = [];
    plan = PLAN;
    GET.mockImplementation((path) => {
      switch (path) {
        case "/api/projects/{name}/tickets":
          return ok({ tickets, invalid: [] });
        case "/api/projects/{name}/plan":
          return ok(plan);
        case "/api/projects/{name}/runs/current":
          return ok({ run: null, phases: [] });
        case "/api/agents":
          return ok({
            backends: [{ installed: true, logged_in: true }],
            graphify: { installed: false, version: null, tested: false },
          });
        case "/api/settings":
          return ok({ secrets: { anthropic: { set: false, source: null } } });
      }
      throw new Error(`unexpected GET ${path}`);
    });
  });

  it("groups in order, hides empty groups, collapses Done and marks Next", async () => {
    tickets = [
      ticket("T01", "done"),
      ticket("T02", "ready"),
      ticket("T03", "ready"),
      ticket(
        "T04",
        "blocked",
        {},
        {
          attempts: 3,
          tokens: 182_000,
          cost_micro_usd: null,
          run_id: 4,
          reason: "gates failed 3 times",
        },
      ),
      ticket(
        "T05",
        "awaiting_approval",
        {},
        {
          attempts: 1,
          tokens: 0,
          cost_micro_usd: 840_000,
          run_id: 5,
          reason: "diff 612 lines > 400",
        },
      ),
      ticket("T06", "running"),
    ];
    show(project({ next_ticket: "T03" }));

    await screen.findByText("Title T02");
    expect(groups()).toEqual([
      "awaiting_approval",
      "blocked",
      "running",
      "ready",
      "done",
    ]);
    expect(rows()).toEqual(["T05", "T04", "T06", "T02", "T03"]); // Done collapsed
    const next = screen.getByText("Next").closest("tr");
    expect(next).toHaveAttribute("data-ticket", "T03");
    const blocked = within(
      document.querySelector('tr[data-ticket="T04"]') as HTMLElement,
    );
    expect(blocked.getByText("gates failed 3 times")).toBeInTheDocument();
    expect(blocked.getByText("182k tokens")).toBeInTheDocument();
    expect(blocked.getByText("Blocked")).toBeInTheDocument();
    expect(screen.getByText("diff 612 lines > 400")).toBeInTheDocument();
    expect(screen.getByText("$0.84")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /Done/ }));
    expect(rows()).toContain("T01");
    expect(screen.getByRole("checkbox", { name: "Show done" })).toBeChecked();
  });

  it("starts with Draft, and opens a ticket on a row click", async () => {
    tickets = [ticket("T02", "ready"), ticket("T01", "draft")];
    show();
    await screen.findByText("Title T01");
    expect(groups()).toEqual(["draft", "ready"]);
    await userEvent.click(
      document.querySelector(
        'tr[data-ticket="T02"] td:nth-child(5)',
      ) as Element,
    );
    expect(onOpen).toHaveBeenCalledWith("T02");
  });

  it("draws met dependencies solid and unmet ones outlined", async () => {
    tickets = [
      ticket("T01", "done"),
      ticket("T02", "ready"),
      ticket("T03", "ready", { depends_on: ["T01", "T02"] }),
    ];
    show();
    const row = within(
      (await screen.findByText("Title T03")).closest("tr") as HTMLElement,
    );
    expect(
      row.getByRole("button", { name: "Open T01 (done)" }),
    ).toHaveAttribute("data-met", "true");
    const unmet = row.getByRole("button", { name: "Open T02 (not done yet)" });
    expect(unmet).toHaveAttribute("data-met", "false");
    await userEvent.click(unmet);
    expect(onOpen).toHaveBeenLastCalledWith("T02");
  });

  it("filters by search and phase, and Clear filters resets them", async () => {
    tickets = [
      ticket("T01", "ready", { title: "Repository and tooling" }),
      ticket("T02", "ready", { title: "Backend scaffold", phase: 1 }),
      ticket("T03", "ready", { title: "Frontend scaffold", phase: 1 }),
    ];
    show();
    await screen.findByText("Repository and tooling");

    await userEvent.type(screen.getByLabelText("Search tickets"), "scaffold");
    expect(rows()).toEqual(["T02", "T03"]);
    await userEvent.clear(screen.getByLabelText("Search tickets"));
    await userEvent.type(screen.getByLabelText("Search tickets"), "t01");
    expect(rows()).toEqual(["T01"]);
    await userEvent.clear(screen.getByLabelText("Search tickets"));
    await userEvent.selectOptions(screen.getByLabelText("Phase"), "1");
    expect(rows()).toEqual(["T02", "T03"]);

    await userEvent.type(screen.getByLabelText("Search tickets"), "nothing");
    expect(screen.getByText("No tickets match.")).toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: "Clear filters" }),
    );
    expect(rows()).toEqual(["T01", "T02", "T03"]);
    expect(screen.getByLabelText("Search tickets")).toHaveValue("");
    expect(screen.getByLabelText("Phase")).toHaveValue("");
  });

  it("shows the draft banner's counts, and Approve waits for the problems", async () => {
    tickets = [
      ticket("T07", "draft", { depends_on: ["T09"] }),
      ticket("T09", "draft", { depends_on: ["T07"] }),
      ticket("T12", "draft"),
    ];
    plan = {
      state: "draft",
      generated_at: new Date(Date.now() - 3 * 60_000).toISOString(),
      ticket_count: 24,
      total_h: 61,
      problems: [
        {
          code: "cycle",
          message: "cycle: T07 → T09 → T07",
          ticket_ids: ["T07", "T09"],
        },
        {
          code: "missing_done_when",
          message: "T12 has no 'Done when'",
          ticket_ids: ["T12"],
        },
      ],
    };
    show();

    const banner = await screen.findByRole("region", { name: "Draft plan" });
    expect(banner).toHaveTextContent(
      "Draft plan · 24 tickets · 61 h · generated 3 min ago",
    );
    expect(banner).toHaveTextContent(
      "2 problems to fix before you can approve",
    );
    const approve = screen.getByRole("button", { name: "Approve plan" });
    expect(approve).toBeDisabled();
    expect(approve).toHaveAccessibleDescription("Fix 2 problems first");
    expect(screen.getAllByText("In a cycle")).toHaveLength(2);

    await userEvent.click(
      screen.getByRole("button", { name: "Cycle T07 → T09 → T07" }),
    );
    expect(onOpen).toHaveBeenLastCalledWith("T07");
    await userEvent.click(
      screen.getByRole("button", { name: "T12 has no 'Done when'" }),
    );
    expect(onOpen).toHaveBeenLastCalledWith("T12");
  });

  it("approves a clean plan through the confirm", async () => {
    tickets = [
      ticket("T01", "draft", { review_required: true }),
      ticket("T02", "draft", { depends_on: ["T01"], phase: 1 }),
    ];
    plan = { ...PLAN, state: "draft", ticket_count: 2, total_h: 4 };
    POST.mockImplementation(() => ok({ approved: ["T01", "T02"] }));
    show();

    await userEvent.click(
      await screen.findByRole("button", { name: "Approve plan" }),
    );
    const dialog = screen.getByRole("dialog", { name: "Approve 2 tickets?" });
    expect(within(dialog).getByText("2 in 2 phases")).toBeInTheDocument();
    expect(within(dialog).getByText("Title T01")).toBeInTheDocument(); // first up
    expect(POST).not.toHaveBeenCalled();
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Approve 2 tickets" }),
    );
    expect(POST).toHaveBeenCalledWith("/api/projects/{name}/plan/approve", {
      params: { path: { name: "demo" } },
    });
  });

  it("Re-plan asks first", async () => {
    tickets = [ticket("T01", "draft")];
    plan = { ...PLAN, state: "draft", ticket_count: 1, total_h: 2 };
    POST.mockImplementation(() => ok({ run_id: 1 }));
    show();
    await userEvent.click(
      await screen.findByRole("button", { name: "Re-plan" }),
    );
    const dialog = screen.getByRole("dialog", {
      name: "Re-plan from the spec?",
    });
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Re-plan" }),
    );
    expect(POST).toHaveBeenCalledWith("/api/projects/{name}/plan/generate", {
      params: { path: { name: "demo" } },
    });
  });

  it("without a spec, points to the Spec tab", async () => {
    plan = { ...PLAN, state: "none" };
    show(project({ has_spec: false }));
    expect(
      await screen.findByText(
        "Write a spec first; the planner turns it into tickets.",
      ),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Open Spec" }));
    expect(onOpenSpec).toHaveBeenCalled();
  });

  it("with a spec but no plan, offers Generate plan", async () => {
    plan = { ...PLAN, state: "none" };
    POST.mockImplementation(() => ok({ run_id: 1 }));
    show();
    expect(await screen.findByText("No plan yet.")).toBeInTheDocument();
    const generate = await screen.findByRole("button", {
      name: "Generate plan",
    });
    await vi.waitFor(() => {
      expect(generate).toBeEnabled();
    });
    await userEvent.click(generate);
    expect(POST).toHaveBeenCalledWith("/api/projects/{name}/plan/generate", {
      params: { path: { name: "demo" } },
    });
  });

  it("shows skeleton rows while the planner runs", async () => {
    plan = { ...PLAN, state: "planning" };
    show();
    expect(await screen.findByText("Planner is running")).toBeInTheDocument();
    expect(screen.queryByText("Cancel planning")).toBeNull();
  });

  it("shows loading, then an error with Retry", async () => {
    let fail = true;
    GET.mockImplementation((path) => {
      if (path === "/api/projects/{name}/tickets" && fail) {
        return Promise.reject(
          new DaemonError({ kind: "not_running", port: 8765, message: "down" }),
        );
      }
      return path === "/api/projects/{name}/plan"
        ? ok(plan)
        : ok({ tickets: [ticket("T01", "ready")], invalid: [] });
    });
    show();
    expect(screen.getByText("Loading tickets…")).toBeInTheDocument();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn't load the tickets",
    );
    fail = false;
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("Title T01")).toBeInTheDocument();
  });
});
