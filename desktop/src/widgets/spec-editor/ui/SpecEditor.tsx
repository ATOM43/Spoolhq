import {
  CircleAlert,
  CircleCheck,
  CircleX,
  LoaderCircle,
  PencilLine,
  RotateCw,
  TriangleAlert,
} from "lucide-react";
import { useState, type ReactNode } from "react";

import {
  SPEC_FILE,
  useSpec,
  type ProjectDetail,
  type SpecFile,
} from "@/entities/project";
import type { CurrentRun } from "@/entities/run";
import { Button, Markdown } from "@/shared/ui";

import { useSpecAutosave, type SaveState } from "../model/autosave";
import { planBlocker, planState, useGeneratePlan } from "../model/plan";
import { PlanButton, PlanFailure } from "./PlanBar";

export const STARTER_OUTLINE = `# Objective
What should exist when this project is done?

# Background
Who it is for, and what already exists.

# Requirements
- …

# Deliverables
- …`;

type View = "split" | "source" | "preview";
const VIEWS: Record<View, string> = {
  split: "Split",
  source: "Source",
  preview: "Preview",
};

const SAVE_LOOK: Record<SaveState, { icon: ReactNode; label: string }> = {
  saved: { icon: <CircleCheck className="text-success" />, label: "Saved" },
  saving: {
    icon: <LoaderCircle className="animate-spin text-accent" />,
    label: "Saving…",
  },
  unsaved: {
    icon: <PencilLine className="text-ink-muted" />,
    label: "Unsaved changes",
  },
  conflict: {
    icon: <TriangleAlert className="text-warning" />,
    label: "Conflict",
  },
  error: { icon: <CircleX className="text-danger" />, label: "Error" },
};

interface EditorProps {
  project: ProjectDetail;
  run: CurrentRun | undefined;
  /** Planning… View: go to the Tickets tab. */
  onViewPlan: () => void;
}

/** V2 · Spec tab: CONTEXT.md with a live preview, autosave and Generate plan. */
export function SpecEditor(props: EditorProps) {
  const spec = useSpec(props.project.name);
  if (spec.isPending) {
    return (
      <p className="flex items-center gap-2 p-4 text-sm text-ink-muted">
        <LoaderCircle aria-hidden className="size-4 animate-spin" />
        Loading {SPEC_FILE}…
      </p>
    );
  }
  if (spec.isError) {
    return (
      <div role="alert" className="flex flex-col items-start gap-2 p-4 text-sm">
        <p className="text-danger">
          Couldn't load {SPEC_FILE}: {spec.error.message}
        </p>
        <Button variant="outline" size="sm" onClick={() => void spec.refetch()}>
          <RotateCw aria-hidden />
          Retry
        </Button>
      </div>
    );
  }
  return <Editor {...props} loaded={spec.data} />;
}

function Editor({
  project,
  run,
  onViewPlan,
  loaded,
}: EditorProps & { loaded: SpecFile }) {
  const draft = useSpecAutosave(project.name, loaded);
  const generate = useGeneratePlan(project.name);
  const [view, setView] = useState<View>("split");
  const plan = planState(run);
  const blocker = planBlocker(project, draft.text, draft.state);
  const look = SAVE_LOOK[draft.state];
  const failure =
    generate.error?.message ?? (generate.isPending ? null : plan.failure);
  const start = () => {
    generate.mutate();
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <code className="font-mono text-sm">{SPEC_FILE}</code>
        <span className="flex items-center gap-1.5 text-sm [&_svg]:size-4">
          <span aria-hidden>{look.icon}</span>
          {look.label}
        </span>
        <div
          role="group"
          aria-label="View"
          className="ml-auto inline-flex rounded-md border"
        >
          {(["split", "source", "preview"] as const).map((option) => (
            <Button
              key={option}
              variant={view === option ? "secondary" : "ghost"}
              size="sm"
              aria-pressed={view === option}
              onClick={() => {
                setView(option);
              }}
            >
              {VIEWS[option]}
            </Button>
          ))}
        </div>
        <PlanButton
          project={project}
          plan={plan}
          blocker={blocker}
          pending={generate.isPending}
          onGenerate={start}
          onViewPlan={onViewPlan}
        />
      </div>
      {plan.planning && plan.progress ? (
        <p className="text-sm text-ink-muted">{plan.progress}</p>
      ) : null}

      {draft.conflict ? (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm"
        >
          <TriangleAlert aria-hidden className="size-4 shrink-0 text-warning" />
          <span className="flex-1">{SPEC_FILE} changed on disk</span>
          <Button variant="outline" size="sm" onClick={draft.reload}>
            Reload
          </Button>
          <Button variant="outline" size="sm" onClick={draft.keepMine}>
            Keep mine
          </Button>
        </div>
      ) : null}
      {draft.error ? (
        <p role="alert" className="flex items-center gap-2 text-sm text-danger">
          <CircleAlert aria-hidden className="size-4" />
          Couldn't save: {draft.error}. Edit again or press Ctrl+S to retry.
        </p>
      ) : null}
      {failure ? (
        <PlanFailure reason={failure} blocker={blocker} onRetry={start} />
      ) : null}

      {draft.text === "" ? (
        <p className="text-sm text-ink-muted">
          Paste an existing task description or start from this outline.
        </p>
      ) : null}
      <div
        className={
          view === "split" ? "grid min-h-96 grid-cols-2 gap-3" : "grid min-h-96"
        }
      >
        {view !== "preview" ? (
          <textarea
            aria-label={`${SPEC_FILE} source`}
            value={draft.text}
            placeholder={STARTER_OUTLINE}
            spellCheck
            onChange={(event) => {
              draft.setText(event.target.value);
            }}
            onKeyDown={(event) => {
              if (event.key === "s" && (event.ctrlKey || event.metaKey)) {
                event.preventDefault();
                draft.saveNow();
              }
            }}
            className="min-h-96 resize-none rounded-md border bg-surface p-3 font-mono text-sm outline-none placeholder:text-ink-muted/60 focus-visible:ring-[3px] focus-visible:ring-accent/50"
          />
        ) : null}
        {view !== "source" ? (
          <section
            aria-label="Preview"
            className="min-h-96 overflow-auto rounded-md border bg-surface p-3"
          >
            {draft.text.trim() === "" ? (
              <p className="text-sm text-ink-muted">Nothing to preview yet.</p>
            ) : (
              <Markdown source={draft.text} />
            )}
          </section>
        ) : null}
      </div>
    </div>
  );
}
