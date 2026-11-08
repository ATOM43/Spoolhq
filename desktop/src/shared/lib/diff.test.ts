import { describe, expect, it } from "vitest";

import { parsePatch } from "./diff";

describe("parsePatch", () => {
  it("numbers lines across hunks", () => {
    const lines = parsePatch(
      [
        "@@ -1,3 +1,3 @@ def main():",
        " a",
        "-b",
        "+B",
        " c",
        "@@ -10,2 +10,3 @@",
        " j",
        "+k",
        " l",
      ].join("\n"),
    );
    expect(lines.map((l) => [l.kind, l.old, l.new, l.text])).toEqual([
      ["hunk", null, null, "@@ -1,3 +1,3 @@ def main():"],
      ["context", 1, 1, "a"],
      ["del", 2, null, "b"],
      ["add", null, 2, "B"],
      ["context", 3, 3, "c"],
      ["hunk", null, null, "@@ -10,2 +10,3 @@"],
      ["context", 10, 10, "j"],
      ["add", null, 11, "k"],
      ["context", 11, 12, "l"],
    ]);
  });

  it("reads single-line hunks and a new file", () => {
    const lines = parsePatch("@@ -0,0 +1 @@\n+only\n");
    expect(lines.map((l) => [l.kind, l.old, l.new])).toEqual([
      ["hunk", null, null],
      ["add", null, 1],
    ]);
  });

  it("keeps no-newline-at-end markers as notes", () => {
    const lines = parsePatch(
      "@@ -1 +1 @@\n-old\n\\ No newline at end of file\n+new\n\\ No newline at end of file",
    );
    expect(lines.map((l) => l.kind)).toEqual([
      "hunk",
      "del",
      "note",
      "add",
      "note",
    ]);
    expect(lines[2]?.text).toBe("\\ No newline at end of file");
    expect(lines[3]?.new).toBe(1);
  });

  it("drops the CR of CRLF lines", () => {
    const lines = parsePatch("@@ -1,2 +1,2 @@\r\n a\r\n-b\r\n+c\r\n");
    expect(lines.map((l) => l.text)).toEqual([
      "@@ -1,2 +1,2 @@",
      "a",
      "b",
      "c",
    ]);
  });

  it("gives nothing for an empty patch", () => {
    expect(parsePatch("")).toEqual([]);
  });
});
