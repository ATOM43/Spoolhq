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

  it("reads a role as a name or a mapping", () => {
    const form = formFrom({
      agents: {
        planner: "codex-cli",
        reviewer: { backend: "default", model: "m" },
      },
    });
    expect(form.roles).toEqual({
      planner: { backend: "codex-cli", model: "" },
      implementer: { backend: "", model: "" },
      reviewer: { backend: "", model: "m" },
    });
  });

  it("writes a plain name when a role's model is emptied", () => {
    const base = { agents: { planner: { backend: "codex-cli", model: "m" } } };
    const form = formFrom(base);
    form.roles.planner.model = "";
    expect(withAgents(base, form)).toEqual({
      agents: { planner: "codex-cli" },
    });
  });
});
