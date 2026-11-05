import { ChevronRight } from "lucide-react";

import { describedBy, Field, Input } from "@/shared/ui";

import { PRESETS, type Form } from "../model/form";

/** "More", collapsed: GitHub remote, merge preset and ClickUp list. */
export function More({
  form,
  setForm,
  open,
  setOpen,
  errorFor,
}: {
  form: Form;
  setForm: (form: Form) => void;
  open: boolean;
  setOpen: (open: boolean) => void;
  errorFor: (field: string) => string | null;
}) {
  const preset = PRESETS.find((p) => p.value === form.preset) ?? PRESETS[0];
  return (
    <details
      open={open}
      onToggle={(event) => {
        setOpen(event.currentTarget.open);
      }}
      className="group border-t pt-3"
    >
      <summary className="flex cursor-pointer list-none items-center gap-2 rounded-md outline-none focus-visible:ring-[3px] focus-visible:ring-accent/50 [&::-webkit-details-marker]:hidden">
        <ChevronRight
          aria-hidden
          className="size-4 transition-transform group-open:rotate-90"
        />
        <span className="font-medium">More</span>
        <span className="truncate text-sm text-ink-muted">
          GitHub remote · merge policy: {preset?.label} · ClickUp list
        </span>
      </summary>
      <div className="mt-4 flex flex-col gap-4">
        <Field
          id="project-remote"
          label="GitHub remote (optional)"
          error={errorFor("git_remote")}
        >
          <Input
            id="project-remote"
            value={form.remote}
            placeholder="https://github.com/owner/repo"
            className="font-mono"
            spellCheck={false}
            aria-describedby={describedBy("project-remote")}
            aria-invalid={errorFor("git_remote") !== null}
            onChange={(event) => {
              setForm({ ...form, remote: event.target.value });
            }}
          />
        </Field>
        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1.5 text-sm font-medium">Merge preset</legend>
          {PRESETS.map((option, index) => (
            <label
              key={option.value}
              className="flex items-start gap-2 text-sm"
            >
              <input
                type="radio"
                name="merge-preset"
                id={index === 0 ? "project-preset" : undefined}
                value={option.value}
                checked={form.preset === option.value}
                onChange={() => {
                  setForm({ ...form, preset: option.value });
                }}
                className="mt-1 accent-accent"
              />
              <span>
                {option.label}
                {index === 0 ? " (default)" : ""}
                <span className="block text-ink-muted">{option.help}</span>
              </span>
            </label>
          ))}
          {errorFor("merge_preset") ? (
            <p role="alert" className="text-sm text-danger">
              {errorFor("merge_preset")}
            </p>
          ) : null}
        </fieldset>
        <Field
          id="project-clickup"
          label="ClickUp list id (optional)"
          error={errorFor("clickup_list_id")}
        >
          <Input
            id="project-clickup"
            value={form.clickup}
            className="font-mono"
            spellCheck={false}
            aria-describedby={describedBy("project-clickup")}
            aria-invalid={errorFor("clickup_list_id") !== null}
            onChange={(event) => {
              setForm({ ...form, clickup: event.target.value });
            }}
          />
        </Field>
      </div>
    </details>
  );
}
