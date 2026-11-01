import { FolderX, ListTodo, LoaderCircle, Play, RotateCw } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { useDaemonStatus } from "@/features/daemon-status";
import { SettingsDialog } from "@/features/settings";
import {
  useProject,
  useProjectEvents,
  useSpec,
  type ProjectDetail,
} from "@/entities/project";
import { useCurrentRun } from "@/entities/run";
import { DaemonError } from "@/shared/api";
import {
  Button,
  EmptyState,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/shared/ui";
import {
  DaemonConnectingPanel,
  DaemonDownPanel,
  DaemonErrorPanel,
} from "@/widgets/daemon-down-panel";
import { SpecEditor } from "@/widgets/spec-editor";

import { formatUsage, panelState, type Tab } from "../model/state";
import { ProjectHeader } from "./ProjectHeader";
import { RunControls } from "./RunControls";

/** V2 · Project panel: header with run controls, tabs Spec · Tickets · Run. */
export function ProjectPage() {
  const { id = "" } = useParams();
  const { status, checking, retry } = useDaemonStatus();

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-6">
      {status.state === "ok" ? (
        // Mounted only while the daemon answers, so its queries refetch when it is back.
        <Panel name={id} />
      ) : status.state === "down" ? (
        <DaemonDownPanel
          port={status.port}
          onRetry={retry}
          checking={checking}
        />
      ) : status.state === "error" ? (
        <DaemonErrorPanel
          error={status.error}
          onRetry={retry}
          checking={checking}
        />
      ) : (
        <DaemonConnectingPanel />
      )}
    </div>
  );
}

function Panel({ name }: { name: string }) {
  const project = useProject(name);
  if (project.isPending) {
    return (
      <p className="flex items-center gap-2 text-sm text-ink-muted">
        <LoaderCircle aria-hidden className="size-4 animate-spin" />
        Loading {name}…
      </p>
    );
  }
  if (project.isError) {
    const missing =
      project.error instanceof DaemonError &&
      project.error.detail.kind === "api" &&
      project.error.detail.status === 404;
    return missing ? (
      <EmptyState
        icon={<FolderX aria-hidden />}
        title={`No project named ${name}`}
        description="It may have been deleted, or its workspace moved."
        action={
          <Button asChild>
            <Link to="/">Back to Home</Link>
          </Button>
        }
      />
    ) : (
      <div role="alert" className="flex flex-col items-start gap-2 text-sm">
        <p className="text-danger">
          Couldn't load {name}: {project.error.message}
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void project.refetch()}
        >
          <RotateCw aria-hidden />
          Retry
        </Button>
      </div>
    );
  }
  return <Loaded project={project.data} />;
}

function Loaded({ project }: { project: ProjectDetail }) {
  const current = useCurrentRun(project.name);
  const spec = useSpec(project.name);
  // The project's REST answer came first, so its latest_seq is where the stream starts.
  useProjectEvents([project]);
  const [chosen, setChosen] = useState<Tab | null>(null);

  const ready = !current.isPending && !spec.isPending;
  const specEmpty = (spec.data?.content.trim() ?? "") === "";
  const state = panelState(project, current.data, specEmpty);
  if (ready && chosen === null) {
    setChosen(state.tab); // opening lands on the state's tab (section 8), once
  }
  const usage = formatUsage(current.data);
  const live = current.data?.active ?? false;

  return (
    <>
      <div className="flex flex-col gap-3 border-b pb-3">
        <div className="flex items-start justify-between gap-4">
          <ProjectHeader project={project} usage={usage} />
          <SettingsDialog />
        </div>
        <RunControls
          project={project.name}
          state={state}
          usage={usage}
          offline={
            current.isError
              ? `Couldn't read the run: ${current.error.message}`
              : null
          }
        />
      </div>
      <Tabs
        value={chosen ?? "spec"}
        onValueChange={(value) => {
          setChosen(value as Tab);
        }}
      >
        <TabsList>
          <TabsTrigger value="spec">Spec</TabsTrigger>
          <TabsTrigger value="tickets">Tickets ({project.total})</TabsTrigger>
          <TabsTrigger value="run">
            Run
            {live ? (
              <span className="size-2 rounded-full bg-accent">
                <span className="sr-only"> (live)</span>
              </span>
            ) : null}
          </TabsTrigger>
        </TabsList>
        {/* Kept mounted, so switching tabs never drops an edit that isn't saved yet. */}
        <TabsContent
          value="spec"
          forceMount
          className="data-[state=inactive]:hidden"
        >
          <SpecEditor
            project={project}
            run={current.data}
            onViewPlan={() => {
              setChosen("tickets");
            }}
          />
        </TabsContent>
        <TabsContent value="tickets">
          <EmptyState
            icon={<ListTodo aria-hidden />}
            title="Coming in T21"
            description="The ticket list, plan review and the ticket drawer arrive in T21. Until then, `spool plan show` and `spool plan approve` cover them."
          />
        </TabsContent>
        <TabsContent value="run">
          <EmptyState
            icon={<Play aria-hidden />}
            title="Coming in T22"
            description="The live run view arrives in T22. The header above shows the run's state and controls it."
          />
        </TabsContent>
      </Tabs>
    </>
  );
}
