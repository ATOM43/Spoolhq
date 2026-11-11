import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ProjectSummary } from "../model/queries";
import { ProjectStatus } from "./ProjectStatus";

type Run = NonNullable<ProjectSummary["run"]>;

const RUN: Run = {
  id: 1,
  kind: "ticket",
  ticket_id: "T15",
  status: "running",
  reason: null,
  started_at: "2026-11-05T10:00:00Z",
  ended_at: null,
  reset_at: null,
  progress_note: null,
};

function project(extra: Partial<ProjectSummary>): ProjectSummary {
  return {
    name: "demo",
    done: 2,
    total: 5,
    run_state: "idle",
    needs_you: 0,
    latest_seq: 0,
    draft: 0,
    remaining_h: 3,
    has_spec: true,
    ...extra,
  };
}

const CASES: [string, Partial<ProjectSummary>, string, string][] = [
  [
    "settings invalid",
    {
      run_state: "running",
      settings_error: { file: "/w/p.yaml", field: "a", message: "b" },
    },
    "Settings invalid",
    "lucide-circle-x",
  ],
  [
    "running",
    { run_state: "running", run: RUN, run_step: "gates" },
    "Running T15 · Gates",
    "lucide-loader-circle",
  ],
  [
    "paused by a usage limit",
    {
      run_state: "paused",
      run: { ...RUN, status: "paused", reset_at: "2026-11-05T14:30:00Z" },
    },
    "Paused · usage limit",
    "lucide-circle-pause",
  ],
  [
    "paused by the user",
    { run_state: "paused", run: { ...RUN, status: "paused" } },
    "Paused",
    "lucide-circle-pause",
  ],
  ["needs you", { needs_you: 2 }, "Needs you (2)", "lucide-hand"],
  [
    "no spec",
    { total: 0, done: 0, has_spec: false },
    "No spec yet",
    "lucide-file-pen",
  ],
  // A hand-added ticket: the project runs without a spec.
  [
    "no spec but a ticket",
    { total: 1, done: 0, has_spec: false },
    "Idle",
    "lucide-moon",
  ],
  ["no plan", { total: 0, done: 0 }, "No plan yet", "lucide-file-text"],
  ["plan in draft", { draft: 5 }, "Plan in draft", "lucide-circle-dashed"],
  ["all done", { done: 5 }, "All done", "lucide-circle-check"],
  ["idle", {}, "Idle", "lucide-moon"],
  // A run_state the daemon doesn't send any more still never reads "Unknown".
  ["an unexpected run state", { run_state: "unknown" }, "Idle", "lucide-moon"],
];

describe("ProjectStatus", () => {
  it.each(CASES)("shows %s as icon + label", (_, extra, label, icon) => {
    const { container } = render(<ProjectStatus project={project(extra)} />);
    expect(container).toHaveTextContent(label);
    expect(container.textContent).toBe(label);
    expect(container.querySelector(`svg.${icon}`)).not.toBeNull();
  });
});
