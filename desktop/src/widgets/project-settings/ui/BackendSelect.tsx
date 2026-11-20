import { TriangleAlert } from "lucide-react";
import { useId } from "react";

import { backendLabel, type Backend } from "@/entities/agent";
import { describedBy, Field } from "@/shared/ui";

const SELECT =
  "h-9 rounded-md border bg-surface px-2 text-sm aria-invalid:border-danger";
const TOOLTIP =
  "pointer-events-none absolute top-full left-0 z-50 mt-1 hidden max-w-sm rounded-md bg-ink px-2 py-1 text-xs font-medium text-surface group-hover:block group-focus-visible:block";

/** Why a backend can't run now ("Not installed"), or null when it is ready. */
function markOf(name: string, backends: Backend[]) {
  const backend = backends.find((b) => b.name === name);
  if (!backend) {
    return { label: "Not detected", reason: "SpoolHQ didn't find it." };
  }
  const reason = backend.reason ?? backendLabel(name).login;
  if (!backend.installed) {
    return { label: "Not installed", reason };
  }
  if (!backend.logged_in) {
    return {
      label: name === "claude-agent-sdk" ? "Needs an API key" : "Not logged in",
      reason,
    };
  }
  return null;
}

/** A not-ready backend as icon + label, its reason in a CSS-only tooltip. */
function BackendMark({
  name,
  backends,
}: {
  name: string;
  backends: Backend[];
}) {
  const id = useId();
  const mark = markOf(name, backends);
  if (!mark) {
    return null;
  }
  return (
    <span
      tabIndex={0}
      title={mark.reason}
      aria-describedby={id}
      className="group relative flex w-fit items-center gap-1.5 rounded-md text-sm text-warning outline-none focus-visible:ring-[3px] focus-visible:ring-accent/50"
    >
      <TriangleAlert aria-hidden className="size-4" />
      {backendLabel(name).title}: {mark.label}
      <span id={id} role="tooltip" className={TOOLTIP}>
        {mark.reason}
      </span>
    </span>
  );
}

/** A backend dropdown: the detected backends, each marked if it isn't ready. */
export function BackendSelect({
  label,
  value,
  backends,
  useDefault,
  error,
  onChange,
}: {
  label: string;
  value: string; // "" = Use default
  backends: Backend[];
  /** The default backend's name: adds "Use default (<name>)" first. */
  useDefault?: string;
  error: string | null;
  onChange: (value: string) => void;
}) {
  const id = useId();
  const names = backends.map((b) => b.name);
  // A value project.yaml sets but the daemon didn't detect stays selectable.
  if (value && !names.includes(value)) {
    names.push(value);
  }
  const shown = value || useDefault || "";
  return (
    <div className="flex flex-col gap-1.5">
      <Field id={id} label={label} error={error}>
        <select
          id={id}
          className={SELECT}
          value={value}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? describedBy(id) : undefined}
          onChange={(event) => {
            onChange(event.target.value);
          }}
        >
          {useDefault !== undefined ? (
            <option value="">
              Use default ({backendLabel(useDefault).title})
            </option>
          ) : null}
          {names.map((name) => {
            const mark = markOf(name, backends);
            return (
              <option key={name} value={name} title={mark?.reason}>
                {backendLabel(name).title}
                {mark ? ` (${mark.label.toLowerCase()})` : ""}
              </option>
            );
          })}
        </select>
      </Field>
      {shown ? <BackendMark name={shown} backends={backends} /> : null}
    </div>
  );
}
