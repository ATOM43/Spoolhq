import type { Agents } from "./queries";

export type Backend = Agents["backends"][number];

const LABELS: Record<string, { title: string; login: string }> = {
  "claude-code-cli": {
    title: "Claude Code",
    login: "run `claude` in a terminal to log in",
  },
  "codex-cli": { title: "Codex", login: "run `codex login` in a terminal" },
  "claude-agent-sdk": {
    title: "Claude Agent SDK",
    login: "add an Anthropic API key in Accounts",
  },
};

/** A backend's display name and how to log in to it. */
export function backendLabel(name: string) {
  return LABELS[name] ?? { title: name, login: "log in to it in a terminal" };
}
