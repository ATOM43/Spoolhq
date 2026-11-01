import { FolderOpen, LoaderCircle } from "lucide-react";
import { useState, type SyntheticEvent } from "react";

import { pickFolder } from "@/shared/api";
import { Button, describedBy, Field, Input } from "@/shared/ui";

import { fieldError, useCreateProject, useTemplates } from "../model/api";

type Source = "repo" | "template";

/** Step 1: name and source (an existing repository, or a template into a new folder). */
export function CreateStep({
  onCreated,
  onCancel,
}: {
  onCreated: (name: string) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState("");
  const [source, setSource] = useState<Source>("repo");
  const [repo, setRepo] = useState("");
  const [template, setTemplate] = useState("");
  const create = useCreateProject();
  const templates = useTemplates();

  const failure = create.error ? fieldError(create.error) : null;
  const errorFor = (...fields: string[]) =>
    failure && fields.includes(failure.field) ? failure.message : null;
  const formError =
    create.error &&
    (failure === null ||
      !["name", "repo", "template", "template_ref"].includes(failure.field))
      ? create.error.message
      : null;

  const submit = (event: SyntheticEvent) => {
    event.preventDefault();
    create.mutate(
      {
        name: name.trim(),
        repo: repo.trim(),
        branch: "main",
        ...(source === "template" ? { template } : {}),
      },
      {
        onSuccess: (created) => {
          onCreated(created.name);
        },
      },
    );
  };

  const choose = async () => {
    const title =
      source === "repo"
        ? "Choose the repository"
        : "Choose a new or empty folder";
    const picked = await pickFolder(title);
    if (picked !== null) {
      setRepo(picked);
    }
  };

  const missing =
    name.trim() === ""
      ? "Enter a name."
      : repo.trim() === ""
        ? "Choose a folder."
        : source === "template" && template === ""
          ? "Choose a template."
          : null;

  return (
    <form onSubmit={submit} className="flex flex-col gap-5" noValidate>
      <Field
        id="project-name"
        label="Name"
        hint="Lowercase letters, digits and hyphens, like my-app."
        error={errorFor("name")}
      >
        <Input
          id="project-name"
          value={name}
          autoComplete="off"
          aria-describedby={describedBy("project-name")}
          aria-invalid={errorFor("name") !== null}
          onChange={(event) => {
            setName(event.target.value);
          }}
        />
      </Field>

      <fieldset className="flex flex-col gap-2">
        <legend className="mb-1.5 text-sm font-medium">Start from</legend>
        {(
          [
            ["repo", "An existing git repository"],
            ["template", "A template, generated into a new or empty folder"],
          ] as const
        ).map(([value, label]) => (
          <label key={value} className="flex items-center gap-2 text-sm">
            <input
              type="radio"
              name="project-source"
              value={value}
              checked={source === value}
              onChange={() => {
                setSource(value);
              }}
              className="accent-accent"
            />
            {label}
          </label>
        ))}
      </fieldset>

      {source === "template" ? (
        <Field
          id="project-template"
          label="Template"
          hint={
            templates.isError
              ? `Couldn't load the templates: ${templates.error.message}`
              : templates.data?.find((t) => t.name === template)?.description
          }
          error={errorFor("template", "template_ref")}
        >
          <select
            id="project-template"
            value={template}
            disabled={!templates.isSuccess}
            aria-describedby={describedBy("project-template")}
            aria-invalid={errorFor("template", "template_ref") !== null}
            onChange={(event) => {
              setTemplate(event.target.value);
            }}
            className="h-9 rounded-md border bg-surface px-3 text-sm disabled:opacity-50"
          >
            <option value="">
              {templates.isPending ? "Loading templates…" : "Choose a template"}
            </option>
            {templates.data?.map((t) => (
              <option key={t.name} value={t.name}>
                {t.name}
              </option>
            ))}
          </select>
        </Field>
      ) : null}

      <Field
        id="project-repo"
        label={source === "repo" ? "Repository folder" : "New or empty folder"}
        error={errorFor("repo")}
      >
        <div className="flex gap-2">
          <Input
            id="project-repo"
            value={repo}
            placeholder={
              source === "repo" ? "/path/to/repo" : "/path/to/new-folder"
            }
            aria-describedby={describedBy("project-repo")}
            aria-invalid={errorFor("repo") !== null}
            className="font-mono"
            onChange={(event) => {
              setRepo(event.target.value);
            }}
          />
          <Button type="button" variant="outline" onClick={() => void choose()}>
            <FolderOpen aria-hidden />
            Choose…
          </Button>
        </div>
      </Field>

      {formError ? (
        <p role="alert" className="text-sm text-danger">
          {formError}
        </p>
      ) : null}

      <div className="flex items-center justify-end gap-2">
        {missing && !create.isPending ? (
          <span className="mr-auto text-sm text-ink-muted">{missing}</span>
        ) : null}
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={missing !== null || create.isPending}>
          {create.isPending ? (
            <LoaderCircle aria-hidden className="animate-spin" />
          ) : null}
          {create.isPending ? "Creating…" : "Create project"}
        </Button>
      </div>
    </form>
  );
}
