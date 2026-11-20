/**
 * The Agents section's form and how it maps to `project.yaml`'s `agents`. A model and a
 * base URL belong to a backend (`agents.backends.<name>`), so roles on the same backend
 * share them. Only what the user changed is touched; the daemon writes just those keys.
 */
import { DaemonError } from "@/shared/api";

export const ROLES = ["planner", "implementer", "reviewer"] as const;
export type Role = (typeof ROLES)[number];
export const ROLE_TITLES: Record<Role, string> = {
  planner: "Planner",
  implementer: "Implementer",
  reviewer: "Reviewer",
};
/** `agents.default` when the file doesn't set it (the daemon's model default). */
export const DEFAULT_BACKEND = "claude-code-cli";

export interface BackendFields {
  model: string;
  base_url: string;
}

export interface AgentsForm {
  default: string;
  planner: string; // "" = Use default
  implementer: string;
  reviewer: string;
  backends: Record<string, BackendFields>;
}

type Data = Record<string, unknown>;

function record(value: unknown): Data {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Data)
    : {};
}

function text(value: unknown): string {
  return typeof value === "string" ? value : "";
}

export function formFrom(settings: Data): AgentsForm {
  const agents = record(settings.agents);
  const backends = Object.entries(record(agents.backends)).map(
    ([name, value]) => {
      const entry = record(value);
      return [
        name,
        { model: text(entry.model), base_url: text(entry.base_url) },
      ] as const;
    },
  );
  return {
    default: text(agents.default) || DEFAULT_BACKEND,
    planner: text(agents.planner),
    implementer: text(agents.implementer),
    reviewer: text(agents.reviewer),
    backends: Object.fromEntries(backends),
  };
}

export function backendFor(form: AgentsForm, role: Role): string {
  return form[role] || form.default;
}

export function fieldsOf(form: AgentsForm, backend: string): BackendFields {
  return form.backends[backend] ?? { model: "", base_url: "" };
}

/** `data` with `key` set to `value`, or without `key` when `value` is undefined. */
function put(data: Data, key: string, value: unknown): Data {
  if (value !== undefined) {
    return { ...data, [key]: value };
  }
  return Object.fromEntries(Object.entries(data).filter(([k]) => k !== key));
}

/** `base` with the form's agents applied; unchanged keys keep their values and order. */
export function withAgents(base: Data, form: AgentsForm): Data {
  const before = record(base.agents);
  let agents: Data = { ...before };
  if (form.default !== (text(before.default) || DEFAULT_BACKEND)) {
    agents.default = form.default;
  }
  for (const role of ROLES) {
    agents = put(agents, role, form[role] || undefined);
  }
  let backends: Data = { ...record(before.backends) };
  for (const [name, fields] of Object.entries(form.backends)) {
    let entry: Data = { ...record(backends[name]) };
    for (const key of ["model", "base_url"] as const) {
      entry = put(entry, key, fields[key].trim() || undefined);
    }
    backends = put(
      backends,
      name,
      Object.keys(entry).length > 0 ? entry : undefined,
    );
  }
  const keep = Object.keys(backends).length > 0 || "backends" in before;
  agents = put(agents, "backends", keep ? backends : undefined);
  if (Object.keys(agents).length === 0 && !("agents" in base)) {
    return base;
  }
  return { ...base, agents };
}

export function isDirty(base: Data, form: AgentsForm): boolean {
  return JSON.stringify(withAgents(base, form)) !== JSON.stringify(base);
}

/** A refused save: the daemon's field (dotted, e.g. `agents.reviewer`) and message. */
export interface Problem {
  field: string | null;
  message: string;
}

/** A 422 as a field and its message, without the `project.yaml: <field>: ` prefix. */
export function problemOf(error: unknown): Problem {
  if (!(error instanceof DaemonError)) {
    return { field: null, message: String(error) };
  }
  const detail = error.detail;
  if (detail.kind !== "api" || detail.status !== 422) {
    return { field: null, message: error.message };
  }
  const first = detail.message.split("\n")[0] ?? "";
  const prefix = `project.yaml: ${detail.field ?? ""}: `;
  return {
    field: detail.field,
    message: first.startsWith(prefix) ? first.slice(prefix.length) : first,
  };
}

/** The disk version a 412 sent back, or null if `error` isn't an edit conflict. */
export function conflictOf(
  error: unknown,
): { settings: Data; etag: string } | null {
  if (!(error instanceof DaemonError) || error.detail.kind !== "api") {
    return null;
  }
  const { status, etag, current } = error.detail;
  if (status !== 412 || etag === null) {
    return null;
  }
  return { settings: record(record(current).settings), etag };
}
