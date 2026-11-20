import { ChevronRight } from "lucide-react";
import { useId, useState } from "react";

import { backendLabel, type Backend } from "@/entities/agent";
import { describedBy, Field, Input } from "@/shared/ui";

import {
  fieldsOf,
  ROLE_TITLES,
  type AgentsForm,
  type BackendFields,
  type Role,
  type RoleFields as RoleValues,
} from "../model/agents-form";
import { BackendSelect } from "./BackendSelect";

type ErrorFor = (field: string) => string | null;

function TextField({
  id,
  label,
  hint,
  error,
  value,
  placeholder,
  onChange,
}: {
  id: string;
  label: string;
  hint: string;
  error: string | null;
  value: string;
  placeholder?: string;
  onChange: (value: string) => void;
}) {
  return (
    <Field id={id} label={label} hint={hint} error={error}>
      <Input
        id={id}
        value={value}
        placeholder={placeholder}
        aria-invalid={!!error}
        aria-describedby={describedBy(id)}
        onChange={(event) => {
          onChange(event.target.value);
        }}
      />
    </Field>
  );
}

/** One role: its backend ("Use default" first) and its own model. */
export function RoleFields({
  role,
  form,
  backends,
  errorFor,
  onChange,
}: {
  role: Role;
  form: AgentsForm;
  backends: Backend[];
  errorFor: ErrorFor;
  onChange: (fields: RoleValues) => void;
}) {
  const id = useId();
  const title = ROLE_TITLES[role];
  const fields = form.roles[role];
  return (
    <fieldset className="flex flex-col gap-3 rounded-md border p-4">
      <legend className="px-1 text-sm font-semibold">{title}</legend>
      <BackendSelect
        label={`${title} backend`}
        value={fields.backend}
        useDefault={form.default}
        backends={backends}
        error={errorFor(`agents.${role}`) ?? errorFor(`agents.${role}.backend`)}
        onChange={(backend) => {
          onChange({ ...fields, backend });
        }}
      />
      <TextField
        id={`${id}-model`}
        label={`${title} model`}
        hint="Leave empty to use the backend's model"
        error={errorFor(`agents.${role}.model`)}
        value={fields.model}
        onChange={(model) => {
          onChange({ ...fields, model });
        }}
      />
    </fieldset>
  );
}

/** Under Advanced: each backend's default model and base URL. */
export function BackendDefaults({
  form,
  backends,
  errorFor,
  onChange,
}: {
  form: AgentsForm;
  backends: Backend[];
  errorFor: ErrorFor;
  onChange: (name: string, fields: Partial<BackendFields>) => void;
}) {
  const id = useId();
  const names = [
    ...new Set([...backends.map((b) => b.name), ...Object.keys(form.backends)]),
  ];
  const hasError = names.some(
    (name) =>
      errorFor(`agents.backends.${name}.model`) !== null ||
      errorFor(`agents.backends.${name}.base_url`) !== null,
  );
  const [open, setOpen] = useState(false);
  return (
    <details
      open={open || hasError}
      onToggle={(event) => {
        setOpen(event.currentTarget.open);
      }}
      className="group"
    >
      <summary className="flex cursor-pointer list-none items-center gap-1 text-sm text-ink-muted select-none [&::-webkit-details-marker]:hidden">
        <ChevronRight
          aria-hidden
          className="size-4 transition-transform group-open:rotate-90"
        />
        Advanced
      </summary>
      <div className="mt-3 flex flex-col gap-3">
        {names.map((name, index) => {
          const title = backendLabel(name).title;
          const fields = fieldsOf(form, name);
          const prefix = `agents.backends.${name}`;
          return (
            <fieldset
              key={name}
              className="flex flex-col gap-3 rounded-md border p-4"
            >
              <legend className="px-1 text-sm font-semibold">
                {title} defaults
              </legend>
              <TextField
                id={`${id}-${String(index)}-model`}
                label={`${title} default model`}
                hint={`For roles on ${title} without their own model; empty uses its own default.`}
                error={errorFor(`${prefix}.model`)}
                value={fields.model}
                onChange={(model) => {
                  onChange(name, { model });
                }}
              />
              <TextField
                id={`${id}-${String(index)}-url`}
                label={`${title} base URL`}
                hint="A custom endpoint, e.g. a local Ollama. Plain http only for localhost."
                error={errorFor(`${prefix}.base_url`)}
                value={fields.base_url}
                placeholder="https://…"
                onChange={(base_url) => {
                  onChange(name, { base_url });
                }}
              />
            </fieldset>
          );
        })}
      </div>
    </details>
  );
}
