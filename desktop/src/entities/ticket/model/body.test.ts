import { describe, expect, it } from "vitest";

import { joinBody, splitBody, splitDoneWhen } from "./body";

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

describe("splitBody and joinBody", () => {
  const body =
    "## Scope\r\n- a\r\n\r\n## Done when\r\n- [ ] works\r\n\r\n## Notes\r\nkeep\r\n";

  it("cuts around the section and joins back to the same bytes", () => {
    const parts = splitBody(body);
    expect(parts.heading).toBe("## Done when\r\n");
    expect(parts.doneWhen).toBe("- [ ] works\r\n\r\n");
    expect(parts.rest).toBe("## Notes\r\nkeep\r\n");
    expect(Object.values(parts).join("")).toBe(body);
    const typed = (text: string) => text.replace(/\r\n/g, "\n");
    expect(joinBody(parts, typed(parts.scope), typed(parts.doneWhen))).toBe(
      body,
    );
  });

  it("changes only the edited part", () => {
    const parts = splitBody(body);
    const joined = joinBody(parts, "## Scope\n- b", parts.doneWhen);
    expect(joined).toBe(
      "## Scope\n- b\n## Done when\r\n- [ ] works\r\n\r\n## Notes\r\nkeep\r\n",
    );
  });

  it("adds the heading when there was none", () => {
    const parts = splitBody("## Scope\n- a\n");
    expect(parts.heading).toBe("");
    expect(joinBody(parts, "## Scope\n- a\n", "- [ ] works")).toBe(
      "## Scope\n- a\n\n## Done when\n\n- [ ] works",
    );
  });

  it("ignores a heading in fenced code", () => {
    const parts = splitBody("```\n## Done when\n```\n## Done when\n- [ ] x\n");
    expect(parts.scope).toBe("```\n## Done when\n```\n");
    expect(parts.doneWhen).toBe("- [ ] x\n");
  });
});
