/** One "Done when" checklist item, as written in the ticket. */
export interface DoneItem {
  text: string;
  checked: boolean;
}

const HEADING = /^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$/;
const ITEM = /^[ \t]*[-*+][ \t]+\[([ xX])\](?:[ \t]+(.*?))?[ \t]*$/;
const FENCE = /^ {0,3}(`{3,}|~{3,})/;

/**
 * The body without its `## Done when` section, and that section's checklist items.
 * Same rules as the daemon's parser (`services/tickets/checklist.py`): the section runs
 * to the next heading of the same or a higher level; fenced code is skipped.
 */
export function splitDoneWhen(body: string): {
  scope: string;
  doneWhen: DoneItem[];
} {
  const kept: string[] = [];
  const doneWhen: DoneItem[] = [];
  let level: number | null = null;
  let found = false;
  let fence: string | null = null;
  for (const line of body.split("\n")) {
    const marker = FENCE.exec(line)?.[1];
    if (marker !== undefined) {
      if (fence === null) {
        fence = marker;
      } else if (marker[0] === fence[0] && marker.length >= fence.length) {
        fence = null;
      }
    }
    const heading =
      fence === null && marker === undefined ? HEADING.exec(line) : null;
    if (heading) {
      const depth = heading[1]?.length ?? 0;
      if (level !== null && depth <= level) {
        level = null;
      }
      if (
        level === null &&
        !found &&
        heading[2]?.toLowerCase() === "done when"
      ) {
        level = depth;
        found = true;
        continue;
      }
    }
    if (level === null) {
      kept.push(line);
      continue;
    }
    const item = fence === null ? ITEM.exec(line) : null;
    if (item) {
      doneWhen.push({ text: item[2] ?? "", checked: item[1] !== " " });
    }
  }
  return { scope: kept.join("\n").trim(), doneWhen };
}

/** A body cut around its `## Done when` section; the four parts join back to it. */
export interface BodyParts {
  /** Everything before the heading (the whole body when there is none). */
  scope: string;
  /** The heading line with its line break; empty when there is none. */
  heading: string;
  /** The section's text, up to the next heading of the same or a higher level. */
  doneWhen: string;
  /** Everything after the section, kept as it is. */
  rest: string;
}

export function splitBody(body: string): BodyParts {
  const lines = body.split("\n");
  let offset = 0;
  let fence: string | null = null;
  let start: number | null = null; // the heading's offset
  let level = 0;
  let sectionStart = 0;
  for (const line of lines) {
    const next = offset + line.length + 1;
    const clean = line.replace(/\r$/, "");
    const marker = FENCE.exec(clean)?.[1];
    if (marker !== undefined) {
      if (fence === null) {
        fence = marker;
      } else if (marker[0] === fence[0] && marker.length >= fence.length) {
        fence = null;
      }
    }
    const heading =
      fence === null && marker === undefined ? HEADING.exec(clean) : null;
    if (heading) {
      const depth = heading[1]?.length ?? 0;
      if (start !== null && depth <= level) {
        return {
          scope: body.slice(0, start),
          heading: body.slice(start, sectionStart),
          doneWhen: body.slice(sectionStart, offset),
          rest: body.slice(offset),
        };
      }
      if (start === null && heading[2]?.toLowerCase() === "done when") {
        start = offset;
        level = depth;
        sectionStart = Math.min(next, body.length);
      }
    }
    offset = next;
  }
  return start === null
    ? { scope: body, heading: "", doneWhen: "", rest: "" }
    : {
        scope: body.slice(0, start),
        heading: body.slice(start, sectionStart),
        doneWhen: body.slice(sectionStart),
        rest: "",
      };
}

/** Text as a textarea shows it: the browser turns every CRLF into LF. */
export const asTyped = (text: string) => text.replace(/\r\n/g, "\n");

/**
 * The body with an edited scope and "Done when"; a part left as it was keeps its
 * exact bytes, so an edit to one part changes nothing else in the file.
 */
export function joinBody(
  parts: BodyParts,
  scope: string,
  doneWhen: string,
): string {
  const lineEnd = (text: string) =>
    text === "" || text.endsWith("\n") ? text : `${text}\n`;
  let start = scope === asTyped(parts.scope) ? parts.scope : scope;
  let heading = parts.heading;
  let section =
    doneWhen === asTyped(parts.doneWhen) ? parts.doneWhen : doneWhen;
  if (heading === "" && section.trim() !== "") {
    start = start.trim() === "" ? "" : `${start.replace(/\s*$/, "")}\n\n`;
    heading = "## Done when\n\n";
  }
  if (heading !== "") {
    start = lineEnd(start);
    section = parts.rest === "" ? section : lineEnd(section);
  }
  return start + heading + section + parts.rest;
}
