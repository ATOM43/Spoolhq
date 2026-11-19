import { useMutation, useQueryClient } from "@tanstack/react-query";
import { LoaderCircle, Wrench, X } from "lucide-react";
import { useEffect, useState, type SyntheticEvent } from "react";
import { flushSync } from "react-dom";

import { useAgents } from "@/entities/agent";
import { queryKeys } from "@/shared/api";
import { Button, ConfirmDialog, ReasonButton, showToast } from "@/shared/ui";

import {
  cancelJob,
  cleanupToast,
  fieldError,
  inspectRepo,
  startJob,
  type Inspection,
  useJob,
  useProjectsDir,
  useTemplates,
} from "../model/api";
import {
  initialForm,
  missing,
  toRequest,
  withInspection,
  withTemplate,
  type Form,
} from "../model/form";
import { Checklist } from "./Checklist";
import { Commands, NameAndRepo, SourceSwitch, TemplateCards } from "./Fields";
import { More } from "./More";
import { RepoNotices } from "./RepoNotices";

/** The element to focus for a request field. */
const FIELD_IDS: Record<string, string> = {
  name: "project-name",
  template: "project-template",
  repo_path: "project-repo",
  "commands.install": "command-install",
  "commands.lint": "command-lint",
  "commands.test": "command-test",
  git_remote: "project-remote",
  merge_preset: "project-preset",
  clickup_list_id: "project-clickup",
};
const IN_MORE = new Set(["git_remote", "merge_preset", "clickup_list_id"]);

/**
 * D1's content: the form, then the job's checklist. `onBusy` says when closing must
 * ask first; `onCreated` gets the new project's name.
 */
export function NewProjectForm({
  onClose,
  onBusy,
  onCreated,
}: {
  onClose: () => void;
  onBusy: (busy: boolean) => void;
  onCreated: (name: string) => void;
}) {
  const queryClient = useQueryClient();
  const templates = useTemplates();
  const projectsDir = useProjectsDir();
  const [form, setForm] = useState(initialForm);
  const [jobId, setJobId] = useState<string | null>(null);
  const [moreOpen, setMoreOpen] = useState(false);
  const [confirming, setConfirming] = useState(false);
  // What inspect said about a picked folder, kept with its path so typing another
  // path drops it.
  const [inspected, setInspected] = useState<{
    path: string;
    found?: Inspection;
    error?: string;
  } | null>(null);
  const graphify = useAgents().data?.graphify.installed;
  const job = useJob(jobId).data;
  const start = useMutation({
    mutationFn: startJob,
    onSuccess: setJobId,
  });

  const first = templates.data?.[0];
  if (form.source === "template" && form.template === "" && first) {
    setForm(withTemplate(form, first)); // the first template is chosen by default
  }

  const running =
    start.isPending ||
    (jobId !== null && job?.state !== "failed" && job?.state !== "cancelled");
  const failed =
    jobId !== null && (job?.state === "failed" || job?.state === "cancelled");

  useEffect(() => {
    onBusy(running);
  }, [running, onBusy]);

  // The list shows the project as "Creating…" once step 1 made it, and drops or
  // refreshes it when the job ends.
  const phase = job ? `${job.state}:${String(job.steps[0]?.state)}` : null;
  useEffect(() => {
    if (phase !== null) {
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects });
    }
  }, [phase, queryClient]);

  useEffect(() => {
    if (job?.state === "succeeded") {
      onCreated(job.project);
    }
  }, [job?.state, job?.project, onCreated]);

  const current =
    form.source === "existing" && inspected?.path === form.repo
      ? inspected
      : null;
  const found = current?.found;

  const inspect = (path: string) => {
    if (form.source !== "existing") {
      return;
    }
    setInspected({ path });
    inspectRepo(path)
      .then((result) => {
        setInspected({ path, found: result });
        setForm((now) =>
          now.repo === path ? withInspection(now, result) : now,
        );
      })
      .catch((error: unknown) => {
        const message =
          fieldError(error)?.message ?? "Couldn't read the repository";
        setInspected({ path, error: message });
      });
  };

  const changeForm = (next: Form) => {
    if (next.source !== form.source) {
      setInspected(null); // a source switch resets the commands it filled in
    }
    setForm(next);
  };

  const apiError = start.error ? fieldError(start.error) : null;
  const errorFor = (field: string) =>
    apiError?.field === field
      ? apiError.message
      : field === "repo_path"
        ? (current?.error ?? null)
        : null;
  const formError =
    start.error && (apiError === null || !(apiError.field in FIELD_IDS))
      ? (apiError?.message ?? start.error.message)
      : null;

  const reason = missing(form, found ? !found.clean : false);

  const submit = (event: SyntheticEvent) => {
    event.preventDefault();
    if (reason === null && !running) {
      start.mutate(toRequest(form));
    }
  };

  const fix = () => {
    const field = job?.steps.find((step) => step.state === "failed")?.field;
    // Rendered at once, so the field is enabled (and shown) before it takes focus.
    flushSync(() => {
      setJobId(null);
      start.reset();
      if (field && IN_MORE.has(field)) {
        setMoreOpen(true);
      }
    });
    document
      .getElementById(FIELD_IDS[field ?? "name"] ?? "project-name")
      ?.focus();
  };

  const close = () => {
    if (running) {
      setConfirming(true);
    } else {
      onClose();
    }
  };

  const stop = () => {
    setConfirming(false);
    if (jobId !== null) {
      void cancelJob(jobId)
        .then((ended) => {
          // The dialog is closed by now; the toast says what the rollback couldn't delete.
          if (ended.rollback && ended.rollback.left.length > 0) {
            showToast(cleanupToast(ended), "error");
          }
        })
        .catch(() => null) // a job that already ended has nothing to stop
        .finally(() => {
          void queryClient.invalidateQueries({ queryKey: queryKeys.projects });
        });
    }
    onClose();
  };

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-5">
      <div className="absolute top-4 right-4">
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          aria-label="Close"
          onClick={close}
        >
          <X aria-hidden />
        </Button>
      </div>
      <fieldset
        disabled={jobId !== null}
        className="flex min-w-0 flex-col gap-5"
      >
        <SourceSwitch
          form={form}
          setForm={changeForm}
          templates={templates.data}
        />
        {form.source === "template" ? (
          <TemplateCards
            form={form}
            setForm={setForm}
            templates={templates}
            error={errorFor("template")}
          />
        ) : null}
        <NameAndRepo
          form={form}
          setForm={setForm}
          projectsDir={projectsDir.data}
          errorFor={errorFor}
          onPicked={inspect}
        />
        {found ? <RepoNotices found={found} graphify={graphify} /> : null}
        <Commands
          form={form}
          setForm={setForm}
          job={job}
          errorFor={errorFor}
          detectedFrom={found?.commands.source ?? undefined}
        />
        <More
          form={form}
          setForm={setForm}
          open={moreOpen}
          setOpen={setMoreOpen}
          errorFor={errorFor}
          remoteHint={
            found?.origin && form.remote === found.origin
              ? "Detected from origin"
              : undefined
          }
        />
      </fieldset>
      {job ? <Checklist job={job} form={form} /> : null}
      {formError ? (
        <p role="alert" className="text-sm text-danger">
          {formError}
        </p>
      ) : null}
      <div className="-mx-6 -mb-6 flex justify-end gap-2 border-t px-6 py-3">
        <Button type="button" variant="outline" onClick={close}>
          Cancel
        </Button>
        {failed ? (
          <Button type="button" onClick={fix}>
            <Wrench aria-hidden />
            Fix
          </Button>
        ) : running ? (
          <Button type="button" disabled>
            <LoaderCircle aria-hidden className="animate-spin" />
            Creating…
          </Button>
        ) : (
          <ReasonButton type="submit" reason={reason}>
            Create project
          </ReasonButton>
        )}
      </div>
      <ConfirmDialog
        open={confirming}
        title="Stop and remove what was created?"
        consequence="Creation stops, and the workspace and any folder this job made are deleted. An existing repo is left as it is."
        action="Stop and remove"
        destructive
        onConfirm={stop}
        onCancel={() => {
          setConfirming(false);
        }}
      />
    </form>
  );
}
