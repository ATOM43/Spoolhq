import { useQueryClient } from "@tanstack/react-query";
import {
  CircleAlert,
  CircleCheck,
  CircleDashed,
  LoaderCircle,
  PencilLine,
  RotateCw,
  TriangleAlert,
} from "lucide-react";
import { useEffect, useState } from "react";

import { useAgents, type Backend } from "@/entities/agent";
import {
  saveSettings,
  useProjectSettings,
  type SettingsFile,
} from "@/entities/project";
import { openSettings } from "@/features/settings";
import { queryKeys } from "@/shared/api";
import { Button, EmptyState, ReasonButton } from "@/shared/ui";

import {
  conflictOf,
  fieldsOf,
  formFrom,
  isDirty,
  problemOf,
  ROLES,
  withAgents,
  type AgentsForm,
  type BackendFields,
  type Problem,
} from "../model/agents-form";
import { BackendDefaults, RoleFields } from "./AgentFields";
import { BackendSelect } from "./BackendSelect";

interface Props {
  project: string;
  /** Told whenever the form gets or loses unsaved changes. */
  onDirtyChange: (dirty: boolean) => void;
}

function Failure({ text, onRetry }: { text: string; onRetry: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-start gap-2 p-6 text-sm">
      <p className="text-danger">{text}</p>
      <Button variant="outline" size="sm" onClick={onRetry}>
        <RotateCw aria-hidden />
        Retry
      </Button>
    </div>
  );
}

function Loading({ text }: { text: string }) {
  return (
    <p className="flex items-center gap-2 p-6 text-sm text-ink-muted">
      <LoaderCircle aria-hidden className="size-4 animate-spin" />
      {text}
    </p>
  );
}

/** V2 · Settings tab: the project's own settings; T47 has the Agents section only. */
export function ProjectSettings({ project, onDirtyChange }: Props) {
  const settings = useProjectSettings(project);
  const agents = useAgents();
  if (settings.isPending) {
    return <Loading text="Loading project.yaml…" />;
  }
  if (settings.isError) {
    return (
      <Failure
        text={`Couldn't load project.yaml: ${settings.error.message}`}
        onRetry={() => void settings.refetch()}
      />
    );
  }
  if (agents.isPending) {
    return <Loading text="Looking for coding agents…" />;
  }
  if (agents.isError) {
    return (
      <Failure
        text={`Couldn't list the agents: ${agents.error.message}`}
        onRetry={() => void agents.refetch()}
      />
    );
  }
  if (agents.data.backends.length === 0) {
    return (
      <EmptyState
        icon={<CircleDashed aria-hidden />}
        title="No coding agents found"
        description="Install Claude Code or Codex and log in, or add an Anthropic API key, then pick one here."
        action={
          <Button
            onClick={() => {
              openSettings("agents");
            }}
          >
            Open App settings
          </Button>
        }
      />
    );
  }
  return (
    <AgentsSection
      project={project}
      loaded={settings.data}
      backends={agents.data.backends}
      onDirtyChange={onDirtyChange}
    />
  );
}

function AgentsSection({
  project,
  loaded,
  backends,
  onDirtyChange,
}: Props & { loaded: SettingsFile; backends: Backend[] }) {
  const queryClient = useQueryClient();
  const [saved, setSaved] = useState(loaded);
  const [form, setForm] = useState(() => formFrom(loaded.settings));
  const [saving, setSaving] = useState(false);
  const [problem, setProblem] = useState<Problem | null>(null);
  const [conflict, setConflict] = useState<SettingsFile | null>(null);
  const dirty = isDirty(saved.settings, form);

  useEffect(() => {
    onDirtyChange(dirty);
  }, [dirty, onDirtyChange]);
  useEffect(
    () => () => {
      onDirtyChange(false);
    },
    [onDirtyChange],
  );

  const edit = (next: AgentsForm) => {
    setForm(next);
    setProblem(null); // a new edit tries again
  };
  const editBackend = (name: string, fields: Partial<BackendFields>) => {
    edit({
      ...form,
      backends: {
        ...form.backends,
        [name]: { ...fieldsOf(form, name), ...fields },
      },
    });
  };

  // Mine applied onto `base`: the other keys stay as `base` has them.
  const save = async (base: SettingsFile) => {
    setSaving(true);
    setProblem(null);
    try {
      const next = await saveSettings(
        project,
        withAgents(base.settings, form),
        base.etag,
      );
      setSaved(next);
      setForm(formFrom(next.settings));
      queryClient.setQueryData(queryKeys.projectSettings(project), next);
      // The project's settings_error and run controls may change.
      void queryClient.invalidateQueries({
        queryKey: queryKeys.project(project),
      });
    } catch (failure) {
      const disk = conflictOf(failure);
      if (disk) {
        setConflict(disk);
      } else {
        setProblem(problemOf(failure));
      }
    } finally {
      setSaving(false);
    }
  };

  const errorFor = (field: string) =>
    problem?.field === field ? problem.message : null;
  const shownFields = [
    "agents.default",
    ...ROLES.flatMap((role) => [
      `agents.${role}`,
      `agents.${role}.backend`,
      `agents.${role}.model`,
    ]),
    ...[...backends.map((b) => b.name), ...Object.keys(form.backends)].flatMap(
      (name) => [
        `agents.backends.${name}.model`,
        `agents.backends.${name}.base_url`,
      ],
    ),
  ];
  const otherProblem =
    problem && !shownFields.includes(problem.field ?? "") ? problem : null;

  return (
    <div className="overflow-auto">
      <div className="mx-auto flex max-w-3xl flex-col gap-6 p-6">
        {conflict ? (
          <div
            role="alert"
            className="flex items-center gap-2 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm"
          >
            <TriangleAlert
              aria-hidden
              className="size-4 shrink-0 text-warning"
            />
            <span className="flex-1">project.yaml changed on disk</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSaved(conflict);
                setForm(formFrom(conflict.settings));
                setConflict(null);
                setProblem(null);
                queryClient.setQueryData(
                  queryKeys.projectSettings(project),
                  conflict,
                );
              }}
            >
              Reload
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setConflict(null);
                setSaved(conflict);
                void save(conflict);
              }}
            >
              Keep mine
            </Button>
          </div>
        ) : null}
        <section
          aria-labelledby="agents-heading"
          className="flex flex-col gap-5"
        >
          <div className="flex flex-col gap-1">
            <h2 id="agents-heading" className="text-lg font-semibold">
              Agents
            </h2>
            <p className="text-sm text-ink-muted">
              Which coding agent each role uses in this project. Saved to its
              project.yaml in the workspace, never in the repo.
            </p>
          </div>
          <BackendSelect
            label="Default backend"
            value={form.default}
            backends={backends}
            error={errorFor("agents.default")}
            onChange={(value) => {
              edit({ ...form, default: value });
            }}
          />
          {ROLES.map((role) => (
            <RoleFields
              key={role}
              role={role}
              form={form}
              backends={backends}
              errorFor={errorFor}
              onChange={(fields) => {
                edit({ ...form, roles: { ...form.roles, [role]: fields } });
              }}
            />
          ))}
          <BackendDefaults
            form={form}
            backends={backends}
            errorFor={errorFor}
            onChange={editBackend}
          />
          {otherProblem ? (
            <p
              role="alert"
              className="flex items-center gap-2 text-sm text-danger"
            >
              <CircleAlert aria-hidden className="size-4 shrink-0" />
              Couldn't save:{" "}
              {otherProblem.field ? `${otherProblem.field}: ` : ""}
              {otherProblem.message}
            </p>
          ) : null}
          <div className="flex items-center gap-3">
            <ReasonButton
              reason={
                saving
                  ? "Saving…"
                  : conflict
                    ? "Reload or keep yours first"
                    : dirty
                      ? null
                      : "No changes to save"
              }
              onClick={() => void save(saved)}
            >
              Save
            </ReasonButton>
            <span className="flex items-center gap-1.5 text-sm text-ink-muted [&_svg]:size-4">
              {dirty ? (
                <>
                  <PencilLine aria-hidden />
                  Unsaved changes
                </>
              ) : (
                <>
                  <CircleCheck aria-hidden className="text-success" />
                  Saved
                </>
              )}
            </span>
          </div>
        </section>
        <p className="text-sm text-ink-muted">
          Other project settings come in a later version; for now edit
          project.yaml.
        </p>
      </div>
    </div>
  );
}
