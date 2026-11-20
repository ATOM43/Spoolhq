import {
  CircleAlert,
  Ellipsis,
  FolderOpen,
  LoaderCircle,
  RotateCw,
  Settings,
} from "lucide-react";
import { Link } from "react-router";

import {
  ProjectStatus,
  settingsErrorLine,
  useProjectEvents,
  useProjects,
  type ProjectSummary,
} from "@/entities/project";
import { NewProjectButton } from "@/features/project-create";
import { formatUsage, timeAgo } from "@/shared/lib";
import {
  Button,
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  EmptyState,
  ProgressLine,
} from "@/shared/ui";

import { NeedsYou } from "./NeedsYou";

const NO_PROJECTS: ProjectSummary[] = [];

export function ProjectsSection() {
  const projects = useProjects();
  const all = projects.data ?? NO_PROJECTS;
  // A creation whose rollback left paths behind is only a Needs-you card.
  const list = all.filter((project) => project.run_state !== "cleanup_failed");
  // A project being created has no event stream yet; the dialog refreshes the list.
  useProjectEvents(list.filter((project) => project.run_state !== "creating"));

  if (projects.isPending) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <LoaderCircle aria-hidden className="size-5 animate-spin" />
            Loading projects…
          </CardTitle>
        </CardHeader>
      </Card>
    );
  }
  if (projects.isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle
            className="flex items-center gap-2"
            role="heading"
            aria-level={2}
          >
            <CircleAlert aria-hidden className="size-5 text-danger" />
            Couldn't load the projects
          </CardTitle>
          <CardDescription>{projects.error.message}</CardDescription>
        </CardHeader>
        <CardFooter>
          <Button
            onClick={() => void projects.refetch()}
            disabled={projects.isFetching}
          >
            <RotateCw
              aria-hidden
              className={projects.isFetching ? "animate-spin" : undefined}
            />
            Retry
          </Button>
        </CardFooter>
      </Card>
    );
  }
  if (all.length === 0) {
    return (
      <EmptyState
        icon={<FolderOpen aria-hidden />}
        title="No projects yet"
        description="A project turns a spec into tickets and code."
        action={<NewProjectButton />}
      />
    );
  }
  return (
    <>
      <NeedsYou projects={all} />
      <section
        aria-labelledby="projects-heading"
        className="flex flex-col gap-3"
      >
        <h2
          id="projects-heading"
          className="flex items-baseline gap-3 text-lg font-semibold"
        >
          Projects
          <span className="text-sm font-normal text-ink-muted">
            {list.length === 1
              ? "1 project"
              : `${String(list.length)} projects`}
          </span>
        </h2>
        <ul className="grid grid-cols-[repeat(auto-fill,320px)] gap-4">
          {list.map((project) => (
            <li key={project.name}>
              <ProjectCard project={project} />
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}

/** A 320 px project card: name, template, progress, status, last activity and usage. */
function ProjectCard({ project }: { project: ProjectSummary }) {
  const problem = settingsErrorLine(project);
  const usage = formatUsage(
    project.usage?.tokens ?? 0,
    project.usage?.cost_usd,
  );
  const active = project.run_state === "running";
  return (
    <div className="relative h-full">
      <Link
        to={`/p/${project.name}`}
        className="flex h-full flex-col gap-3 rounded-lg border bg-surface p-4 outline-none hover:border-ink-muted/40 focus-visible:ring-[3px] focus-visible:ring-accent/50"
      >
        <div className="flex items-center justify-between gap-2 pr-8">
          <span className="truncate font-semibold">{project.name}</span>
          <span className="shrink-0 rounded bg-surface-sunken px-1.5 font-mono text-xs text-ink-muted">
            {project.template ?? "existing repo"}
          </span>
        </div>
        <ProgressLine
          done={project.done}
          total={project.total}
          remainingH={project.remaining_h}
        />
        {problem ? (
          <p className="truncate text-sm text-danger" title={problem}>
            {problem}
          </p>
        ) : null}
        <div className="mt-auto flex items-center justify-between gap-2 text-sm">
          <ProjectStatus project={project} />
          <span className="shrink-0 text-ink-muted">
            {[
              active
                ? "Active now"
                : project.last_activity
                  ? timeAgo(project.last_activity)
                  : null,
              usage,
            ]
              .filter(Boolean)
              .join(" · ")}
          </span>
        </div>
      </Link>
      <CardMenu project={project.name} />
    </div>
  );
}

/** The card's ⋯ menu, beside the card's link (a link can't hold another). */
function CardMenu({ project }: { project: string }) {
  return (
    <details className="group absolute top-3 right-3">
      <summary
        aria-label={`${project} actions`}
        className="flex size-7 cursor-pointer list-none items-center justify-center rounded-md text-ink-muted outline-none hover:bg-surface-sunken focus-visible:ring-[3px] focus-visible:ring-accent/50 [&::-webkit-details-marker]:hidden"
      >
        <Ellipsis aria-hidden className="size-4" />
      </summary>
      <div className="absolute top-full right-0 z-50 mt-1 min-w-44 rounded-md border bg-surface p-1 shadow-md">
        <Link
          to={`/p/${project}?tab=settings`}
          className="flex items-center gap-2 rounded px-2 py-1.5 text-sm outline-none hover:bg-surface-sunken focus-visible:bg-surface-sunken"
        >
          <Settings aria-hidden className="size-4" />
          Project settings
        </Link>
      </div>
    </details>
  );
}
