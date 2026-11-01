import { KeyRound, LoaderCircle, RotateCw } from "lucide-react";
import { useId, useState, type SyntheticEvent } from "react";

import { Button, describedBy, Field, Input, ReasonButton } from "@/shared/ui";

import {
  removeSecret,
  storeSecret,
  useDaemonSettings,
  useRefreshSecrets,
  type DaemonSettings,
  type SecretName,
} from "../model/queries";

const SECRETS: { name: SecretName; label: string; hint: string }[] = [
  {
    name: "anthropic",
    label: "Anthropic API key",
    hint: "Optional: only the Claude Agent SDK backend needs it.",
  },
  {
    name: "github",
    label: "GitHub token",
    hint: "For pull requests and syncing a project with GitHub.",
  },
  { name: "clickup", label: "ClickUp token", hint: "For the ClickUp tracker." },
];

type Status = DaemonSettings["secrets"][string];

function statusLabel(status: Status | undefined): string {
  if (!status?.set) {
    return "Not set";
  }
  return status.source === "env" ? "Set (env)" : "Set (keychain)";
}

function message(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/** One write-only secret: its status, Replace (or Set) and Remove; never its value. */
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
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fromEnv = status?.set === true && status.source === "env";

  async function act(work: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await work();
      await refresh();
    } catch (failure) {
      setError(message(failure));
    } finally {
      setBusy(false);
    }
  }

  function submit(event: SyntheticEvent) {
    event.preventDefault();
    const secret = value;
    // Drop the value from React state right away; only this request carries it.
    setValue("");
    void act(async () => {
      await storeSecret(name, secret);
      setEditing(false);
    });
  }

  return (
    <li className="flex flex-col gap-2 p-3 text-sm">
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-1.5 font-medium">
          <KeyRound aria-hidden className="size-4 text-ink-muted" />
          {label}
        </span>
        <span className="text-ink-muted">{statusLabel(status)}</span>
      </div>
      <p className="text-xs text-ink-muted">{hint}</p>
      {editing ? (
        <form onSubmit={submit} className="flex flex-col gap-2">
          <Field id={id} label={`New ${label}`} error={error}>
            <Input
              id={id}
              type="password"
              autoComplete="off"
              spellCheck={false}
              value={value}
              aria-describedby={describedBy(id)}
              aria-invalid={!!error}
              onChange={(event) => {
                setValue(event.target.value);
              }}
            />
          </Field>
          <div className="flex gap-2">
            <ReasonButton
              type="submit"
              size="sm"
              reason={
                busy ? "Saving…" : value === "" ? "Paste the value first" : null
              }
            >
              {busy ? (
                <LoaderCircle aria-hidden className="animate-spin" />
              ) : null}
              Save
            </ReasonButton>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setValue("");
                setEditing(false);
                setError(null);
              }}
            >
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <div className="flex flex-col gap-1">
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setEditing(true);
              }}
            >
              {status?.set ? "Replace" : "Set"}
            </Button>
            {status?.set ? (
              <ReasonButton
                variant="outline"
                size="sm"
                reason={
                  fromEnv
                    ? "Set by an environment variable: unset it where the daemon starts"
                    : busy
                      ? "Removing…"
                      : null
                }
                onClick={() => void act(() => removeSecret(name))}
              >
                Remove
              </ReasonButton>
            ) : null}
          </div>
          {error ? (
            <p role="alert" className="text-sm text-danger">
              {error}
            </p>
          ) : null}
        </div>
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
    <div className="flex flex-col gap-2">
      <ul className="flex flex-col divide-y rounded-md border">
        {SECRETS.map((secret) => (
          <SecretRow
            key={secret.name}
            {...secret}
            status={settings.data.secrets[secret.name]}
          />
        ))}
      </ul>
      <p className="text-xs text-ink-muted">
        Stored in your system keychain. A value is never shown again after
        saving.
      </p>
    </div>
  );
}
