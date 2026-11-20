import { describe, expect, it } from "vitest";

import { formFrom, isDirty, withAgents } from "./agents-form";

describe("agents form", () => {
  it("leaves untouched settings exactly as they were", () => {
    const base = {
      name: "demo",
      agents: { backends: {}, default: "codex-cli" },
    };
    expect(withAgents(base, formFrom(base))).toEqual(base);
    expect(isDirty(base, formFrom(base))).toBe(false);
    expect(isDirty({ name: "demo" }, formFrom({ name: "demo" }))).toBe(false);
    expect(withAgents({ name: "demo" }, formFrom({ name: "demo" }))).toEqual({
      name: "demo",
    });
  });

  it("drops a backend entry whose fields are emptied", () => {
    const base = {
      agents: {
        backends: { "codex-cli": { model: "m", base_url: "https://x" } },
      },
    };
    const form = formFrom(base);
    form.backends["codex-cli"] = { model: " ", base_url: "" };
    expect(withAgents(base, form)).toEqual({ agents: { backends: {} } });
  });
});
