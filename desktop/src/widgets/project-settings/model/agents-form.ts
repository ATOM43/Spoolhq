/**
 * The Agents section's form and how it maps to `project.yaml`'s `agents`. A role is a
 * backend name, or `{backend, model}` when it has its own model; each backend's model
 * and base URL (`agents.backends.<name>`) are that backend's defaults. Only what the
 * user changed is touched; the daemon writes just those keys.
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

export interface RoleFields {
  backend: string; // "" = Use default
  model: string; // "" = the backend's model
}

export interface AgentsForm {
  default: string;
  roles: Record<Role, RoleFields>;
  backends: Record<string, BackendFields>;
}

/** A role's `backend: default` in a mapping. */
const USE_DEFAULT = "default";

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
    roles: {
      planner: roleFrom(agents.planner),
      implementer: roleFrom(agents.implementer),
      reviewer: roleFrom(agents.reviewer),
    },
    backends: Object.fromEntries(backends),
  };
}

function roleFrom(value: unknown): RoleFields {
  const entry = typeof value === "string" ? { backend: value } : record(value);
  const backend = text(entry.backend);
  return {
    backend: backend === USE_DEFAULT ? "" : backend,
    model: text(entry.model),
  };
}

/** A role as `project.yaml` holds it: a mapping only when it has a model. */
function roleValue(fields: RoleFields, before: unknown): unknown {
  const same = roleFrom(before);
  if (same.backend === fields.backend && same.model === fields.model.trim()) {
    return before; // unchanged: keep the file's spelling
  }
  const model = fields.model.trim();
  if (!model) {
    return fields.backend || undefined;
  }
  return fields.backend ? { backend: fields.backend, model } : { model };
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
    agents = put(agents, role, roleValue(form.roles[role], before[role]));
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
