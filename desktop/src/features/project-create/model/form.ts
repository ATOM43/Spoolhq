import type { CreateRequest, Job, JobStep, Template } from "./api";

export type Source = CreateRequest["source"];
export type Gate = "install" | "lint" | "test";
export type MergePreset = NonNullable<CreateRequest["merge_preset"]>;
export const GATES: readonly Gate[] = ["install", "lint", "test"];

export const NAME_RE = /^[a-z][a-z0-9-]{0,39}$/;
export const NAME_RULE =
  "Use lowercase letters, digits and hyphens, starting with a letter";

export const SOURCES: readonly { value: Source; label: string }[] = [
  { value: "template", label: "Template" },
  { value: "existing", label: "Existing repo" },
  { value: "empty", label: "Empty repo" },
];

export const PRESETS: readonly {
  value: MergePreset;
  label: string;
  help: string;
}[] = [
  {
    value: "direct_unless_risky",
    label: "Direct unless risky",
    help: "Merges on its own; large diffs and protected paths wait for you.",
  },
  {
    value: "always_pr",
    label: "Always pull request",
    help: "Every ticket waits for you, as a pull request when there is a remote.",
  },
  {
    value: "always_direct",
    label: "Always direct",
    help: "Merges without asking, unless the reviewer says it needs a person.",
  },
];

export interface Form {
  source: Source;
  template: string;
  name: string;
  repo: string;
  commands: Record<Gate, string>;
  remote: string;
  preset: MergePreset;
  clickup: string;
}

export const NO_COMMANDS: Record<Gate, string> = {
  install: "",
  lint: "",
  test: "",
};

export function initialForm(): Form {
  return {
    source: "template",
    template: "",
    name: "",
    repo: "",
    commands: NO_COMMANDS,
    remote: "",
    preset: "direct_unless_risky",
    clickup: "",
  };
}

/** The form with `template` chosen and its commands filled in. */
export function withTemplate(form: Form, template: Template): Form {
  return {
    ...form,
    template: template.name,
    commands: { ...template.commands },
  };
}

/** Why Create is disabled, or null. */
export function missing(form: Form): string | null {
  if (form.name === "") {
    return "Enter a project name";
  }
  if (!NAME_RE.test(form.name)) {
    return NAME_RULE;
  }
  if (form.source === "template" && form.template === "") {
    return "Choose a template";
  }
  if (form.repo.trim() === "") {
    return "Choose the repo folder";
  }
  if (
    form.source !== "empty" &&
    GATES.some((gate) => form.commands[gate].trim() === "")
  ) {
    return "Set the install, lint and test commands";
  }
  return null;
}

const optional = (text: string) => (text.trim() === "" ? null : text.trim());

export function toRequest(form: Form): CreateRequest {
  return {
    name: form.name,
    source: form.source,
    repo_path: form.repo.trim(),
    template: form.source === "template" ? form.template : null,
    commands: {
      install: optional(form.commands.install),
      lint: optional(form.commands.lint),
      test: optional(form.commands.test),
    },
    git_remote: optional(form.remote),
    merge_preset: form.preset,
    clickup_list_id: optional(form.clickup),
  };
}

/** A step's title for this job: the repo step says what it does for the source. */
export function stepTitle(step: JobStep, form: Form, job: Job): string {
  if (step.name === "repo") {
    return job.source === "template"
      ? `Generate from ${form.template}`
      : job.source === "existing"
        ? "Prepare repo"
        : "Init repo";
  }
  if (
    step.name === "commands" &&
    step.state !== "pending" &&
    step.state !== "skipped"
  ) {
    const total = GATES.filter(
      (gate) => form.commands[gate].trim() !== "",
    ).length;
    return `${step.title} · ${String(step.passed.length)} of ${String(total)} passed`;
  }
  return step.title;
}

/** Each command's state while the commands step runs or after it, for its field. */
export function gateState(
  job: Job | undefined,
  form: Form,
  gate: Gate,
): "passed" | "running" | "failed" | null {
  const step = job?.steps.find((s) => s.name === "commands");
  if (!step) {
    return null;
  }
  if (step.passed.includes(gate)) {
    return "passed";
  }
  if (step.state === "failed" && step.field === `commands.${gate}`) {
    return "failed";
  }
  const next = GATES.find(
    (g) => form.commands[g].trim() !== "" && !step.passed.includes(g),
  );
  return step.state === "running" && next === gate ? "running" : null;
}
