import { FolderX, ListTodo, LoaderCircle, Play, RotateCw } from "lucide-react";
import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router";

import { useDaemonStatus } from "@/features/daemon-status";
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

import { formatUsage, guidance, panelState, type Tab } from "../model/state";
import { ProjectHeader } from "./ProjectHeader";
import { RunControls } from "./RunControls";
import { SettingsBar } from "./SettingsBar";

/** V2 · Project panel: header with run controls, tabs Spec · Tickets · Run. */
export function ProjectPage() {
  const { id = "" } = useParams();
  const { status, checking, retry } = useDaemonStatus();

  return (
    <div className="flex h-full min-h-0 flex-col">
      {status.state === "ok" ? (
        // Mounted only while the daemon answers, so its queries refetch when it is back.
        <Panel name={id} />
      ) : (
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-6 py-16">
          {status.state === "down" ? (
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
      )}
    </div>
  );
}

function Panel({ name }: { name: string }) {
  const project = useProject(name);
  if (project.isPending) {
    return (
      <p className="flex items-center gap-2 px-6 py-6 text-sm text-ink-muted">
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
      <div
        role="alert"
        className="flex flex-col items-start gap-2 px-6 py-6 text-sm"
      >
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
  return (
    <Loaded
      project={project.data}
      reloading={project.isFetching}
      onReload={() => void project.refetch()}
    />
  );
}

const TAB_LIST =
  "h-auto w-full justify-start gap-6 rounded-none border-b bg-transparent px-6 py-0";
const TAB =
  "h-10 flex-none rounded-none border-0 border-b-2 border-transparent px-0 data-[state=active]:border-accent data-[state=active]:bg-transparent data-[state=active]:shadow-none";
const TABS: readonly Tab[] = ["spec", "tickets", "run"];

function Loaded({
  project,
  reloading,
  onReload,
}: {
  project: ProjectDetail;
  reloading: boolean;
  onReload: () => void;
}) {
  const current = useCurrentRun(project.name);
  const spec = useSpec(project.name);
  // The project's REST answer came first, so its latest_seq is where the stream starts.
  useProjectEvents([project]);
  const [params] = useSearchParams();
  const asked = TABS.find((tab) => tab === params.get("tab")) ?? null;
  const [chosen, setChosen] = useState<Tab | null>(asked);

  const ready = !current.isPending && !spec.isPending;
  const specEmpty = (spec.data?.content.trim() ?? "") === "";
  const state = panelState(project, current.data, specEmpty);
  if (ready && chosen === null) {
    setChosen(state.tab); // opening lands on the state's tab (section 8), once
  }
  const live = current.data?.active ?? false;

  return (
    <>
      <div className="flex flex-col gap-2 px-6 pt-4 pb-2">
        <ProjectHeader project={project} />
        <div className="flex flex-wrap items-start justify-between gap-4">
          <p className="pt-2 text-sm text-ink-muted">
            {guidance(project, state)}
          </p>
          <RunControls
            project={project.name}
            state={state}
            usage={formatUsage(current.data)}
            offline={
              project.settings_error
                ? "Fix project.yaml first"
                : current.isError
                  ? `Couldn't read the run: ${current.error.message}`
                  : null
            }
          />
        </div>
      </div>
      <SettingsBar
        project={project}
        reloading={reloading}
        onReload={onReload}
      />
      <Tabs
        value={chosen ?? "spec"}
        onValueChange={(value) => {
          setChosen(value as Tab);
        }}
        className="min-h-0 flex-1 gap-0"
      >
        <TabsList className={TAB_LIST}>
          <TabsTrigger value="spec" className={TAB}>
            Spec
          </TabsTrigger>
          <TabsTrigger value="tickets" className={TAB}>
            Tickets <span className="text-ink-muted">{project.total}</span>
          </TabsTrigger>
          <TabsTrigger value="run" className={TAB}>
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
          className="flex min-h-0 flex-col data-[state=inactive]:hidden"
        >
          <SpecEditor
            project={project}
            run={current.data}
            onViewPlan={() => {
              setChosen("tickets");
            }}
          />
        </TabsContent>
        <TabsContent value="tickets" className="overflow-auto p-6">
          <EmptyState
            icon={<ListTodo aria-hidden />}
            title="Coming in T21"
            description="The ticket list, plan review and the ticket drawer arrive in T21. Until then, `spool plan show` and `spool plan approve` cover them."
          />
        </TabsContent>
        <TabsContent value="run" className="overflow-auto p-6">
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
