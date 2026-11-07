import { describe, expect, it } from "vitest";

import type { RunEvent } from "@/entities/run";

import { mergedCommit, stepStates, toolTarget, toRows } from "./transcript";

let seq = 0;
const ev = (type: string, data: Record<string, unknown> = {}): RunEvent => {
  seq += 1;
  return {
    seq,
    run_id: 1,
    attempt: 1,
    ticket: "T01",
    type,
    ts: new Date(Date.UTC(2026, 10, 7, 14, 0, 0, seq * 100)).toISOString(),
    data,
  };
};

describe("toolTarget", () => {
  it("takes the command, file or pattern, else the raw text", () => {
    expect(toolTarget('{"command": "just test"}')).toBe("just test");
    expect(toolTarget('{"file_path": "a.py", "content": "x"}')).toBe("a.py");
    expect(toolTarget('{"pattern": "TODO"}')).toBe("TODO");
    expect(toolTarget('{"command": "cut off')).toBe('{"command": "cut off');
  });
});

describe("toRows", () => {
  it("joins a result to its call with the duration, and keeps the order", () => {
    const rows = toRows([
      ev("agent.tool_call", {
        id: "a",
        name: "Bash",
        input_summary: '{"command": "ls"}',
      }),
      ev("agent.message", { text: "hi" }),
      ev("agent.tool_result", { id: "a", text: "x", lines: 1, is_error: true }),
      ev("agent.tool_result", { id: "unknown", text: "y", lines: 1 }),
      ev("agent.warning", { text: "bad line", line: "{" }),
      ev("agent.rate_limit", { status: "allowed_warning", reset_at: null }),
      ev("agent.rate_limit", { status: "allowed", reset_at: null }),
      ev("step", { step: "gates", state: "running" }),
    ]);
    expect(rows.map((row) => row.kind)).toEqual([
      "tool",
      "message",
      "note",
      "note",
    ]);
    const tool = rows[0];
    expect(tool?.kind === "tool" && tool.seconds).toBeCloseTo(0.2);
    expect(tool?.kind === "tool" && tool.result?.isError).toBe(true);
  });

  it("notes a usage-limit pause and a new attempt", () => {
    const rows = toRows([
      ev("attempt.started", { number: 2, kind: "gate_retry" }),
      ev("run.status", { to: "paused", reset_at: "2026-11-07T14:30:00Z" }),
      ev("run.status", { to: "paused", reset_at: null }),
    ]);
    expect(rows.map((row) => row.kind === "note" && row.text)).toEqual([
      "Attempt 2 started (gate retry)",
      expect.stringMatching(/^Paused by a usage limit · resumes /),
    ]);
  });
});

describe("stepStates", () => {
  it("takes each step's latest state, and earlier steps count as passed", () => {
    const states = stepStates([
      ev("step", { step: "implement", state: "running" }),
      ev("step", { step: "implement", state: "passed" }),
      ev("step", { step: "gates", state: "failed" }),
      ev("step", { step: "bogus", state: "passed" }),
    ]);
    expect(states).toEqual({
      worktree: "passed",
      implement: "passed",
      gates: "failed",
      review: "pending",
      policy: "pending",
      integrate: "pending",
    });
  });

  it("is all pending before any step", () => {
    expect(Object.values(stepStates([]))).toEqual(Array(6).fill("pending"));
  });
});

it("mergedCommit takes the integrate event's short sha", () => {
  expect(mergedCommit([ev("integrate", { commit: "abcdef123456" })])).toBe(
    "abcdef1",
  );
  expect(mergedCommit([])).toBeNull();
});
