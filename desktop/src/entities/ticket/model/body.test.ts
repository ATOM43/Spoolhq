import { describe, expect, it } from "vitest";

import { splitDoneWhen } from "./body";

describe("splitDoneWhen", () => {
  it("takes the section out, up to the next heading of its level", () => {
    const body = [
      "## Scope",
      "- a",
      "## Done when",
      "- [ ] first",
      "- [X] second",
      "### Notes",
      "- [ ] nested still counts",
      "## After",
      "- [ ] not an item",
    ].join("\n");
    expect(splitDoneWhen(body)).toEqual({
      scope: "## Scope\n- a\n## After\n- [ ] not an item",
      doneWhen: [
        { text: "first", checked: false },
        { text: "second", checked: true },
        { text: "nested still counts", checked: false },
      ],
    });
  });

  it("ignores headings and items inside fenced code", () => {
    const body = [
      "```md",
      "## Done when",
      "- [ ] fake",
      "```",
      "## Done when",
      "~~~",
      "- [ ] fenced",
      "~~~",
      "- [ ] real",
    ].join("\n");
    const { scope, doneWhen } = splitDoneWhen(body);
    expect(doneWhen).toEqual([{ text: "real", checked: false }]);
    expect(scope).toBe("```md\n## Done when\n- [ ] fake\n```");
  });

  it("has no items without the section", () => {
    expect(splitDoneWhen("Just text")).toEqual({
      scope: "Just text",
      doneWhen: [],
    });
  });
});
