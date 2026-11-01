import { FlaskConical, LoaderCircle, RotateCw } from "lucide-react";
import { useState, type SyntheticEvent } from "react";

import { Button, describedBy, Field, Input } from "@/shared/ui";

import {
  fieldError,
  GATES,
  saveCommands,
  testCommand,
  useProjectSettings,
  type CommandTestResult,
  type Gate,
  type ProjectSettings,
} from "../model/api";
import { CommandResult } from "./CommandResult";

const LABELS: Record<Gate, string> = {
  install: "Install",
  lint: "Lint",
  test: "Test",
};

/** Step 2: the project's install, lint and test commands, each with **Test**. */
export function CommandsStep({
  name,
  onDone,
}: {
  name: string;
  onDone: () => void;
}) {
  const settings = useProjectSettings(name);

  if (settings.isPending) {
    return (
      <p className="flex items-center gap-2 text-sm text-ink-muted">
        <LoaderCircle aria-hidden className="size-4 animate-spin" />
        Loading the project's commands…
      </p>
    );
  }
  if (settings.isError) {
    return (
      <div className="flex flex-col gap-4">
        <p role="alert" className="text-sm text-danger">
          Couldn't load the project's commands: {settings.error.message}
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onDone}>
            Close
          </Button>
          <Button onClick={() => void settings.refetch()}>
            <RotateCw aria-hidden />
            Retry
          </Button>
        </div>
      </div>
    );
  }
  return <CommandsForm name={name} loaded={settings.data} onDone={onDone} />;
}

function initial(loaded: ProjectSettings): Record<Gate, string> {
  const commands = (loaded.settings.commands ?? {}) as Partial<
    Record<Gate, unknown>
  >;
  const text = (gate: Gate) =>
    typeof commands[gate] === "string" ? commands[gate] : "";
  return { install: text("install"), lint: text("lint"), test: text("test") };
}

function CommandsForm({
  name,
  loaded,
  onDone,
}: {
  name: string;
  loaded: ProjectSettings;
  onDone: () => void;
}) {
  const [commands, setCommands] = useState(() => initial(loaded));
  const [results, setResults] = useState<
    Partial<Record<Gate, CommandTestResult>>
  >({});
  const [errors, setErrors] = useState<Partial<Record<Gate, string>>>({});
  const [testing, setTesting] = useState<Partial<Record<Gate, boolean>>>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const runTest = async (gate: Gate) => {
    setTesting((t) => ({ ...t, [gate]: true }));
    setErrors((e) => ({ ...e, [gate]: undefined }));
    setResults((r) => ({ ...r, [gate]: undefined }));
    try {
      const result = await testCommand(name, gate, commands[gate].trim());
      setResults((r) => ({ ...r, [gate]: result }));
    } catch (error) {
      const message = fieldError(error)?.message ?? (error as Error).message;
      setErrors((e) => ({ ...e, [gate]: message }));
    } finally {
      setTesting((t) => ({ ...t, [gate]: false }));
    }
  };

  const save = async (event: SyntheticEvent) => {
    event.preventDefault();
    setSaving(true);
    setSaveError(null);
    try {
      const trimmed = {
        install: commands.install.trim(),
        lint: commands.lint.trim(),
        test: commands.test.trim(),
      };
      await saveCommands(name, loaded, trimmed);
      onDone();
    } catch (error) {
      setSaveError((error as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const empty = GATES.find((gate) => commands[gate].trim() === "");

  return (
    <form
      onSubmit={(event) => void save(event)}
      className="flex flex-col gap-5"
      noValidate
    >
      <p className="text-sm text-ink-muted">
        Project <span className="font-mono text-ink">{name}</span> is created.
        These commands are the gates every ticket must pass.{" "}
        <strong>Test</strong> runs one in the repository now, without a shell
        (up to 90 s).
      </p>
      {GATES.map((gate) => {
        const id = `command-${gate}`;
        const blank = commands[gate].trim() === "";
        return (
          <div key={gate} className="flex flex-col gap-2">
            <Field
              id={id}
              label={LABELS[gate]}
              error={errors[gate] ?? null}
              hint={blank ? "Enter a command to test it." : undefined}
            >
              <div className="flex gap-2">
                <Input
                  id={id}
                  value={commands[gate]}
                  className="font-mono"
                  aria-describedby={describedBy(id)}
                  aria-invalid={errors[gate] !== undefined}
                  onChange={(event) => {
                    const value = event.target.value;
                    setCommands((c) => ({ ...c, [gate]: value }));
                  }}
                />
                <Button
                  type="button"
                  variant="outline"
                  aria-label={`Test ${LABELS[gate]}`}
                  disabled={blank || testing[gate] === true}
                  onClick={() => void runTest(gate)}
                >
                  {testing[gate] ? (
                    <LoaderCircle aria-hidden className="animate-spin" />
                  ) : (
                    <FlaskConical aria-hidden />
                  )}
                  {testing[gate] ? "Testing…" : "Test"}
                </Button>
              </div>
            </Field>
            {results[gate] ? <CommandResult result={results[gate]} /> : null}
          </div>
        );
      })}
      {saveError ? (
        <p role="alert" className="text-sm text-danger">
          {saveError}
        </p>
      ) : null}
      <div className="flex items-center justify-end gap-2">
        {empty ? (
          <span className="mr-auto text-sm text-ink-muted">
            Enter the {LABELS[empty].toLowerCase()} command to save.
          </span>
        ) : null}
        <Button type="button" variant="ghost" onClick={onDone}>
          Keep as is
        </Button>
        <Button type="submit" disabled={empty !== undefined || saving}>
          {saving ? (
            <LoaderCircle aria-hidden className="animate-spin" />
          ) : null}
          {saving ? "Saving…" : "Save commands"}
        </Button>
      </div>
    </form>
  );
}
