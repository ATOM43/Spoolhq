import {
  CircleCheck,
  CircleDashed,
  Info,
  LoaderCircle,
  OctagonX,
  RotateCw,
} from "lucide-react";
import { useId, useState, type SyntheticEvent } from "react";

import { Button, describedBy, Input, ReasonButton } from "@/shared/ui";

import {
  removeSecret,
  storeSecret,
  testSecret,
  useDaemonSettings,
  useRefreshSecrets,
  type DaemonSettings,
  type SecretName,
} from "../model/queries";

const SECRETS: { name: SecretName; label: string; hint: string }[] = [
  {
    name: "anthropic",
    label: "Anthropic API key",
    hint: "Only the Claude Agent SDK backend needs it. Coding CLIs use their own login.",
  },
  {
    name: "github",
    label: "GitHub token",
    hint: "Needed to push to GitHub and open pull requests. Local git works without it.",
  },
  {
    name: "clickup",
    label: "ClickUp token",
    hint: "Mirrors tickets to a ClickUp list. You can add it later.",
  },
];

type Status = DaemonSettings["secrets"][string];
type Tested = { ok: boolean; message: string };

function statusLabel(status: Status | undefined): string {
  if (!status?.set) {
    return "Not set";
  }
  return status.source === "env" ? "Set (env)" : "Set (keychain)";
}

function message(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function TestResult({ result }: { result: Tested }) {
  return result.ok ? (
    <p role="status" className="flex items-center gap-1.5 text-success">
      <CircleCheck aria-hidden className="size-4" />
      {result.message} · tested just now
    </p>
  ) : (
    <p role="status" className="flex items-center gap-1.5 text-danger">
      <OctagonX aria-hidden className="size-4" />
      {result.message}
    </p>
  );
}

/** One write-only secret: a password field with Save, Test and Remove; never its value. */
function SecretRow({
  name,
  label,
  hint,
  status,
}: {
  name: SecretName;
  label: string;
  hint: string;
  status: Status | undefined;
}) {
  const id = useId();
  const refresh = useRefreshSecrets();
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Not stored anywhere else: it's gone when the dialog closes.
  const [tested, setTested] = useState<Tested | null>(null);
  const set = status?.set === true;
  const fromEnv = set && status.source === "env";

  async function act(doing: string, work: () => Promise<void>) {
    setBusy(doing);
    setError(null);
    setTested(null);
    try {
      await work();
    } catch (failure) {
      setError(message(failure));
    } finally {
      setBusy(null);
    }
  }

  function submit(event: SyntheticEvent) {
    event.preventDefault();
    const secret = value;
    // Drop the value from React state right away; only this request carries it.
    setValue("");
    void act("Saving…", async () => {
      await storeSecret(name, secret);
      await refresh();
    });
  }

  return (
    <li className="flex flex-col gap-1.5 text-sm">
      <div className="flex items-center justify-between gap-2">
        <label htmlFor={id} className="font-medium">
          {label}
          <span aria-hidden className="ml-2 font-normal text-ink-muted">
            Optional
          </span>
        </label>
        <span className="flex items-center gap-1 text-ink-muted">
          {set ? (
            <CircleCheck aria-hidden className="size-4 text-success" />
          ) : (
            <CircleDashed aria-hidden className="size-4" />
          )}
          {statusLabel(status)}
        </span>
      </div>
      <form onSubmit={submit} className="flex gap-2">
        <Input
          id={id}
          type="password"
          autoComplete="off"
          spellCheck={false}
          placeholder={
            set ? "Saved · paste a new value to replace it" : "Not set"
          }
          value={value}
          aria-describedby={describedBy(id)}
          aria-invalid={!!error}
          className="flex-1 font-mono"
          onChange={(event) => {
            setValue(event.target.value);
          }}
        />
        <ReasonButton
          type="submit"
          reason={busy ?? (value === "" ? "Paste the value first" : null)}
        >
          {busy === "Saving…" ? (
            <LoaderCircle aria-hidden className="animate-spin" />
          ) : null}
          Save
        </ReasonButton>
        <ReasonButton
          type="button"
          variant="outline"
          reason={busy ?? (set ? null : "Save a value first")}
          onClick={() =>
            void act("Testing…", async () => {
              setTested(await testSecret(name));
            })
          }
        >
          {busy === "Testing…" ? (
            <LoaderCircle aria-hidden className="animate-spin" />
          ) : null}
          Test
        </ReasonButton>
        {set ? (
          <ReasonButton
            type="button"
            variant="outline"
            reason={
              fromEnv
                ? "Set by an environment variable: unset it where the daemon starts"
                : busy
            }
            onClick={() =>
              void act("Removing…", async () => {
                await removeSecret(name);
                await refresh();
              })
            }
          >
            Remove
          </ReasonButton>
        ) : null}
      </form>
      {tested ? <TestResult result={tested} /> : null}
      {error ? (
        <p id={describedBy(id)} role="alert" className="text-danger">
          {error}
        </p>
      ) : (
        <p id={describedBy(id)} className="text-xs text-ink-muted">
          {hint}
        </p>
      )}
    </li>
  );
}

/** D2 · Accounts: write-only secrets, stored in the system keychain by the daemon. */
export function AccountsTab() {
  const settings = useDaemonSettings();
  if (settings.isPending) {
    return (
      <p className="flex items-center gap-2 text-sm text-ink-muted">
        <LoaderCircle aria-hidden className="size-4 animate-spin" />
        Loading accounts…
      </p>
    );
  }
  if (settings.isError) {
    return (
      <div role="alert" className="flex flex-col items-start gap-2 text-sm">
        <p className="text-danger">
          Couldn't load the accounts: {settings.error.message}
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void settings.refetch()}
        >
          <RotateCw aria-hidden />
          Retry
        </Button>
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-5">
      <p className="flex items-start gap-2 rounded-md bg-accent/10 p-3 text-sm">
        <Info aria-hidden className="mt-0.5 size-4 shrink-0" />
        Keys and tokens are stored in your system keychain, never in project
        files. A value is never shown again after saving.
      </p>
      <ul className="flex flex-col gap-5">
        {SECRETS.map((secret) => (
          <SecretRow
            key={secret.name}
            {...secret}
            status={settings.data.secrets[secret.name]}
          />
        ))}
      </ul>
    </div>
  );
}
