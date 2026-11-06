import { useState } from "react";

type CopyState = "idle" | "copied" | "failed";

/** Copy `text` to the clipboard; `state` says whether it worked. */
export function useCopy(text: string) {
  const [state, setState] = useState<CopyState>("idle");
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setState("copied");
    } catch {
      setState("failed");
    }
  }
  return { state, copy };
}
