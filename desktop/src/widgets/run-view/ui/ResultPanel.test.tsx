import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { RunDetail } from "@/entities/run";

import { hasResult } from "../model/format";
import { ResultPanel } from "./ResultPanel";

function run(extra: Partial<RunDetail>): RunDetail {
  return {
    id: 7,
    kind: "ticket",
    ticket_id: "T15",
    status: "running",
    reason: null,
    started_at: "2026-11-07T14:00:00Z",
    ended_at: null,
    reset_at: null,
    progress_note: null,
    attempts: [],
    ...extra,
  };
}

function show(detail: RunDetail, next: string | null = null) {
  const calls = { open: vi.fn(), next: vi.fn() };
  render(
    <ResultPanel
      run={detail}
      commit="a1b2c3d"
      next={next}
      onViewNext={calls.next}
      onOpenTicket={calls.open}
      runNext={<button type="button">Run next (T11)</button>}
    />,
  );
  return calls;
}

describe("ResultPanel", () => {
  it("merged, with the next ticket", async () => {
    const calls = show(run({ status: "done" }), "T16");
    expect(screen.getByText("Merged as a1b2c3d")).toBeInTheDocument();
    expect(screen.getByText("· Next: T16 started")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "View T16" }));
    expect(calls.next).toHaveBeenCalled();
  });

  it("blocked: the reason, and Unblock opens the drawer", async () => {
    const calls = show(
      run({ status: "blocked", reason: "gates failed after 3 retries" }),
    );
    expect(
      screen.getByText("Blocked: gates failed after 3 retries"),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Unblock" }));
    expect(calls.open).toHaveBeenCalledWith("T15");
  });

  it("needs approval: the rule, and Review opens the drawer", async () => {
    const calls = show(
      run({
        status: "awaiting_approval",
        reason: "diff 612 lines exceeds 400",
      }),
    );
    expect(
      screen.getByText("Needs approval: diff 612 lines exceeds 400"),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Review" }));
    expect(calls.open).toHaveBeenCalledWith("T15");
  });

  it("paused by a usage limit resumes by itself", () => {
    const resets = "2026-11-07T14:30:00Z";
    const time = new Date(resets).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    show(run({ status: "paused", reset_at: resets }));
    expect(screen.getByText(`Paused · resumes ${time}`)).toBeInTheDocument();
    expect(
      screen.getByText("The run continues by itself."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it.each([
    ["cancelled", "Cancelled"],
    ["interrupted", "Interrupted: The daemon stopped"],
  ])("%s offers Run next", (status, text) => {
    show(run({ status, reason: "the daemon stopped" }));
    expect(screen.getByText(text)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Run next (T11)" }),
    ).toBeInTheDocument();
  });

  it("is shown only once a run has a result", () => {
    expect(hasResult(run({ status: "running" }))).toBe(false);
    expect(hasResult(run({ status: "paused" }))).toBe(false);
    expect(hasResult(run({ status: "paused", reset_at: "x" }))).toBe(true);
    expect(hasResult(run({ status: "blocked" }))).toBe(true);
  });
});
