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
