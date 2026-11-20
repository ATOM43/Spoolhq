import { describe, expect, it } from "vitest";

import { DaemonError } from "@/shared/api";

import { batchError, draftsOf, type DraftJob } from "./drafting";

const job = (problems: { code: string; message: string; field: string }[]) =>
  ({
    id: "j1",
    project: "demo",
    state: "succeeded",
    error: null,
    run_id: 1,
    drafts: [
      {
        ref: "D1",
        title: "A",
        scope: "",
        done_when: [],
        depends_on: ["T09"],
        estimate_h: 2,
        review_required: false,
        phase: -1,
        problems,
      },
    ],
  }) as DraftJob;

describe("draftsOf", () => {
  it("puts problems on form fields, and the rest in notes that don't block", () => {
    const [d] = draftsOf(
      job([
        {
          code: "unknown_dependency",
          message: "T09 doesn't exist",
          field: "depends_on",
        },
        { code: "cycle", message: "D1 → T09 → D1", field: "depends_on" },
        {
          code: "missing_done_when",
          message: "Add an item",
          field: "done_when",
        },
        { code: "schema", message: "phase: must be 0 or more", field: "phase" },
      ]),
    );
    expect(d?.problems).toEqual({
      dependsOn: "T09 doesn't exist; D1 → T09 → D1",
      doneWhen: "Add an item",
    });
    expect(d?.notes).toEqual(["Left out: phase: must be 0 or more"]);
    expect(d?.phase).toBeNull();
  });
});

describe("batchError", () => {
  const error = (field: string | null) =>
    new DaemonError({
      kind: "api",
      status: 422,
      code: "validation_error",
      message: "nope",
      field,
      etag: null,
      current: null,
    });

  it("names the draft and the form's field", () => {
    expect(batchError(error("tickets.2.estimate_h"))).toEqual({
      index: 2,
      field: "estimate",
      message: "nope",
    });
  });

  it("anything else goes on the form", () => {
    expect(batchError(error(null))).toEqual({
      index: null,
      field: "form",
      message: "nope",
    });
    expect(batchError(new Error("down"))).toEqual({
      index: null,
      field: "form",
      message: "down",
    });
  });
});
