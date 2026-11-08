/** One line of a unified diff, with its line numbers on each side. */
export interface DiffLine {
  kind: "hunk" | "add" | "del" | "context" | "note";
  /** The line without its `+`, `-` or space marker; a hunk or note line whole. */
  text: string;
  old: number | null;
  new: number | null;
}

const HUNK = /^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/;

/**
 * The lines of a patch's hunks (from its first `@@`), numbered across hunks. A `\r`
 * before the newline (a CRLF file) is dropped; `\ No newline at end of file` is a note.
 * Untrusted text: render it as plain text only.
 */
export function parsePatch(patch: string): DiffLine[] {
  const raw = patch.split("\n");
  if (raw.at(-1) === "") {
    raw.pop();
  }
  const lines: DiffLine[] = [];
  let oldNo = 0;
  let newNo = 0;
  for (const item of raw) {
    const line = item.endsWith("\r") ? item.slice(0, -1) : item;
    const hunk = HUNK.exec(line);
    if (hunk) {
      oldNo = Number(hunk[1]);
      newNo = Number(hunk[2]);
      lines.push({ kind: "hunk", text: line, old: null, new: null });
    } else if (line.startsWith("+")) {
      lines.push({ kind: "add", text: line.slice(1), old: null, new: newNo++ });
    } else if (line.startsWith("-")) {
      lines.push({ kind: "del", text: line.slice(1), old: oldNo++, new: null });
    } else if (line.startsWith("\\")) {
      lines.push({ kind: "note", text: line, old: null, new: null });
    } else {
      lines.push({
        kind: "context",
        text: line.slice(1),
        old: oldNo++,
        new: newNo++,
      });
    }
  }
  return lines;
}
