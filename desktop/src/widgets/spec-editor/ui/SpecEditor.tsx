import {
  CircleAlert,
  CircleCheck,
  CircleX,
  FileUp,
  LoaderCircle,
  PencilLine,
  RotateCw,
  TriangleAlert,
} from "lucide-react";
import { useRef, useState, type ReactNode } from "react";

import {
  SPEC_FILE,
  useSpec,
  type ProjectDetail,
  type SpecFile,
} from "@/entities/project";
import type { CurrentRun } from "@/entities/run";
import { Button, ConfirmDialog, Markdown } from "@/shared/ui";

import { useSpecAutosave, type SaveState } from "../model/autosave";
import { wordCount } from "../model/words";
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
  const fileInput = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState<{
    name: string;
    text: string;
  } | null>(null);
  // Read in the webview: no file-system permission, and the text goes through autosave.
  const importFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = () => {
      const text = typeof reader.result === "string" ? reader.result : "";
      if (draft.text.trim() === "") {
        draft.setText(text);
      } else {
        setImporting({ name: file.name, text });
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex flex-wrap items-center gap-3 border-b px-6 py-2">
        <code className="font-mono text-sm">{SPEC_FILE}</code>
        <span className="flex items-center gap-1.5 text-sm [&_svg]:size-4">
          <span aria-hidden>{look.icon}</span>
          {look.label}
        </span>
        <span className="text-sm text-ink-muted">{wordCount(draft.text)}</span>
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
        <input
          ref={fileInput}
          type="file"
          accept=".md,text/markdown"
          aria-label="Markdown file to import"
          tabIndex={-1}
          className="sr-only"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) {
              importFile(file);
            }
            event.target.value = ""; // the same file can be picked again
          }}
        />
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            fileInput.current?.click();
          }}
        >
          <FileUp aria-hidden />
          Import .md
        </Button>
        <PlanButton
          project={project}
          plan={plan}
          blocker={blocker}
          pending={generate.isPending}
          onGenerate={start}
          onViewPlan={onViewPlan}
        />
      </div>
      <ConfirmDialog
        open={importing !== null}
        title={`Replace the spec with ${importing?.name ?? "the file"}?`}
        consequence={`${SPEC_FILE} is replaced by the imported file and saved. The current text is lost.`}
        action="Replace spec"
        onCancel={() => {
          setImporting(null);
        }}
        onConfirm={() => {
          if (importing) {
            draft.setText(importing.text);
          }
          setImporting(null);
        }}
      />
      <div className="flex flex-col gap-2 px-6 py-2 empty:hidden">
        {plan.planning && plan.progress ? (
          <p className="text-sm text-ink-muted">{plan.progress}</p>
        ) : null}

        {draft.conflict ? (
          <div
            role="alert"
            className="flex items-center gap-2 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm"
          >
            <TriangleAlert
              aria-hidden
              className="size-4 shrink-0 text-warning"
            />
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
          <p
            role="alert"
            className="flex items-center gap-2 text-sm text-danger"
          >
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
      </div>
      <div
        className={
          view === "split"
            ? "grid min-h-0 flex-1 grid-cols-2"
            : "grid min-h-0 flex-1"
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
            className="h-full min-h-0 resize-none overflow-auto border-r bg-surface px-6 py-4 font-mono text-sm outline-none placeholder:text-ink-muted/60 focus-visible:ring-[3px] focus-visible:ring-accent/50 focus-visible:ring-inset"
          />
        ) : null}
        {view !== "source" ? (
          <section
            aria-label="Preview"
            className="h-full min-h-0 overflow-auto bg-surface px-8 py-4"
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
