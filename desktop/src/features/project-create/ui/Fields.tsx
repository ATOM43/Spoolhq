import {
  CircleCheck,
  CircleX,
  FolderOpen,
  LayoutTemplate,
  LoaderCircle,
  RotateCw,
} from "lucide-react";
import type { ReactNode } from "react";

import { pickFolder } from "@/shared/api";
import { cn } from "@/shared/lib";
import { Button, describedBy, Field, Input } from "@/shared/ui";

import type { Job, Template } from "../model/api";
import {
  GATES,
  gateState,
  NAME_RE,
  NAME_RULE,
  NO_COMMANDS,
  SOURCES,
  withTemplate,
  type Form,
  type Gate,
} from "../model/form";

type ErrorFor = (field: string) => string | null;

interface Templates {
  data?: Template[] | undefined;
  isPending: boolean;
  isError: boolean;
  refetch: () => unknown;
}

const REPO_HELP = {
  template: "A new or empty folder; its parent must exist",
  empty: "A new or empty folder; its parent must exist",
  existing:
    "The stack commands run in your checkout; files they create (like .venv) stay even if creation fails",
};

export function SourceSwitch({
  form,
  setForm,
  templates,
}: {
  form: Form;
  setForm: (form: Form) => void;
  templates: Template[] | undefined;
}) {
  const choose = (source: Form["source"]) => {
    const first = templates?.[0];
    const reset = { ...form, source, template: "", commands: NO_COMMANDS };
    setForm(
      source === "template" && first ? withTemplate(reset, first) : reset,
    );
  };
  return (
    <div
      role="radiogroup"
      aria-label="Source"
      className="grid grid-cols-3 gap-1 rounded-lg bg-surface-sunken p-1"
    >
      {SOURCES.map(({ value, label }) => (
        <button
          key={value}
          type="button"
          role="radio"
          aria-checked={form.source === value}
          onClick={() => {
            if (form.source !== value) {
              choose(value);
            }
          }}
          className={cn(
            "h-8 rounded-md text-sm outline-none focus-visible:ring-[3px] focus-visible:ring-accent/50",
            form.source === value
              ? "bg-surface font-medium shadow-sm"
              : "text-ink-muted hover:text-ink",
          )}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

export function TemplateCards({
  form,
  setForm,
  templates,
  error,
}: {
  form: Form;
  setForm: (form: Form) => void;
  templates: Templates;
  error: string | null;
}) {
  if (templates.isPending) {
    return (
      <p className="flex items-center gap-2 text-sm text-ink-muted">
        <LoaderCircle aria-hidden className="size-4 animate-spin" />
        Loading templates…
      </p>
    );
  }
  if (templates.isError || !templates.data) {
    return (
      <div className="flex items-center justify-between gap-2 rounded-lg border border-danger/40 p-3">
        <p role="alert" className="flex items-center gap-2 text-sm text-danger">
          <CircleX aria-hidden className="size-4" />
          Couldn't load the templates
        </p>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => void templates.refetch()}
        >
          <RotateCw aria-hidden />
          Retry
        </Button>
      </div>
    );
  }
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="sr-only">Template</legend>
      {templates.data.map((template) => {
        const chosen = form.template === template.name;
        return (
          <label
            key={template.name}
            className={cn(
              "flex cursor-pointer items-start gap-3 rounded-lg border p-3 has-focus-visible:ring-[3px] has-focus-visible:ring-accent/50",
              chosen && "border-accent bg-accent/5",
            )}
          >
            <input
              type="radio"
              name="project-template"
              id={chosen ? "project-template" : undefined}
              className="sr-only"
              checked={chosen}
              onChange={() => {
                setForm(withTemplate(form, template));
              }}
            />
            <LayoutTemplate aria-hidden className="mt-0.5 size-4 text-accent" />
            <span className="flex min-w-0 flex-1 flex-col">
              <span className="font-mono text-sm font-medium">
                {template.name}
              </span>
              <span className="text-sm text-ink-muted">
                {template.summary ?? template.description}
              </span>
            </span>
            <span className="flex shrink-0 items-center gap-1 rounded-md bg-success/10 px-1.5 py-0.5 text-xs font-medium text-success">
              <CircleCheck aria-hidden className="size-3.5" />
              Bundled
            </span>
          </label>
        );
      })}
      {error ? (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      ) : null}
    </fieldset>
  );
}

export function NameAndRepo({
  form,
  setForm,
  projectsDir,
  errorFor,
}: {
  form: Form;
  setForm: (form: Form) => void;
  projectsDir: string | undefined;
  errorFor: ErrorFor;
}) {
  const badName = form.name !== "" && !NAME_RE.test(form.name);
  const nameError = badName ? NAME_RULE : errorFor("name");
  const choose = async () => {
    const picked = await pickFolder(
      form.source === "existing"
        ? "Choose the repository"
        : "Choose a new or empty folder",
    );
    if (picked !== null) {
      setForm({ ...form, repo: picked });
    }
  };
  return (
    <>
      <div className="grid grid-cols-2 gap-4">
        <Field
          id="project-name"
          label="Project name"
          error={nameError}
          hint={form.name ? `Slug: ${form.name}` : undefined}
        >
          <Input
            id="project-name"
            value={form.name}
            autoComplete="off"
            spellCheck={false}
            aria-describedby={describedBy("project-name")}
            aria-invalid={nameError !== null}
            onChange={(event) => {
              setForm({ ...form, name: event.target.value });
            }}
          />
        </Field>
        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium">Workspace</span>
          <p
            aria-label="Workspace"
            className="flex h-9 items-center truncate rounded-md border bg-surface-sunken px-3 font-mono text-sm"
          >
            {`${projectsDir ?? "~/spoolhq-projects"}/${form.name || "<name>"}`}
          </p>
        </div>
      </div>
      <Field
        id="project-repo"
        label="Repo folder"
        hint={REPO_HELP[form.source]}
        error={errorFor("repo_path")}
      >
        <div className="flex gap-2">
          <Input
            id="project-repo"
            value={form.repo}
            className="font-mono"
            spellCheck={false}
            aria-describedby={describedBy("project-repo")}
            aria-invalid={errorFor("repo_path") !== null}
            onChange={(event) => {
              setForm({ ...form, repo: event.target.value });
            }}
          />
          <Button type="button" variant="outline" onClick={() => void choose()}>
            <FolderOpen aria-hidden />
            Choose…
          </Button>
        </div>
      </Field>
    </>
  );
}

const GATE_LOOK: Record<
  "passed" | "running" | "failed",
  [ReactNode, string, string]
> = {
  passed: [<CircleCheck key="i" aria-hidden />, "Passed", "text-success"],
  running: [
    <LoaderCircle key="i" aria-hidden className="animate-spin" />,
    "Running",
    "text-accent",
  ],
  failed: [<CircleX key="i" aria-hidden />, "Failed", "text-danger"],
};

function commandsHelp(source: Form["source"]): string {
  const gates = "Gates run these on every ticket.";
  if (source === "template") {
    return `Filled in from the template. ${gates}`;
  }
  return source === "empty"
    ? `Leave empty to set later in project.yaml. ${gates}`
    : gates;
}

export function Commands({
  form,
  setForm,
  job,
  errorFor,
}: {
  form: Form;
  setForm: (form: Form) => void;
  job: Job | undefined;
  errorFor: ErrorFor;
}) {
  const setCommand = (gate: Gate, value: string) => {
    setForm({ ...form, commands: { ...form.commands, [gate]: value } });
  };
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-2 text-sm font-medium">Stack commands</legend>
      {GATES.map((gate) => {
        const id = `command-${gate}`;
        const error = errorFor(`commands.${gate}`);
        const state = gateState(job, form, gate);
        return (
          <div key={gate} className="flex flex-col gap-1">
            <div className="grid grid-cols-[4rem_1fr_5.5rem] items-center gap-2">
              <label htmlFor={id} className="text-sm text-ink-muted">
                {gate}
              </label>
              <Input
                id={id}
                value={form.commands[gate]}
                className="font-mono"
                spellCheck={false}
                placeholder={
                  form.source === "existing" ? `e.g. just ${gate}` : undefined
                }
                aria-invalid={error !== null}
                aria-describedby={error ? describedBy(id) : undefined}
                onChange={(event) => {
                  setCommand(gate, event.target.value);
                }}
              />
              {state ? (
                <span
                  className={cn(
                    "flex items-center gap-1 text-sm [&_svg]:size-3.5",
                    GATE_LOOK[state][2],
                  )}
                >
                  {GATE_LOOK[state][0]}
                  {GATE_LOOK[state][1]}
                </span>
              ) : (
                <span />
              )}
            </div>
            {error ? (
              <p
                id={describedBy(id)}
                role="alert"
                className="ml-18 text-sm text-danger"
              >
                {error}
              </p>
            ) : null}
          </div>
        );
      })}
      <p className="text-sm text-ink-muted">{commandsHelp(form.source)}</p>
    </fieldset>
  );
}
