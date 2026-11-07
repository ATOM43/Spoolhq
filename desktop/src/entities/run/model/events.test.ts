import { describe, expect, it } from "vitest";

import { mergeEvents, type RunEvent } from "./events";

const ev = (seq: number): RunEvent => ({
  seq,
  run_id: 1,
  attempt: 1,
  ticket: "T01",
  type: "log",
  ts: "2026-11-07T14:00:00Z",
  data: {},
});

describe("mergeEvents", () => {
  it("appends, drops a duplicate seq and sorts a late one in", () => {
    const merged = mergeEvents([ev(1), ev(3)], [ev(4), ev(3), ev(2), ev(4)]);
    expect(merged.map((e) => e.seq)).toEqual([1, 2, 3, 4]);
  });

  it("returns the same list when nothing is new", () => {
    const list = [ev(1)];
    expect(mergeEvents(list, [ev(1)])).toBe(list);
  });
});
