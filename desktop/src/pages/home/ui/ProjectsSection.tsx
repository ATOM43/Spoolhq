import { CircleAlert, FolderOpen, LoaderCircle, RotateCw } from "lucide-react";
import { Link } from "react-router";

import {
  ProjectStatus,
  useProjectEvents,
  useProjects,
  type ProjectSummary,
} from "@/entities/project";
import { NewProjectButton } from "@/features/project-create";
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
  const list = projects.data ?? NO_PROJECTS;
  useProjectEvents(list);

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
  if (list.length === 0) {
    return (
      <EmptyState
        icon={<FolderOpen aria-hidden />}
        title="No projects yet"
        description="A project links a git repository to its spec, tickets and runs."
        action={<NewProjectButton />}
      />
    );
  }
  return (
    <>
      <NeedsYou projects={list} />
      <section
        aria-labelledby="projects-heading"
        className="flex flex-col gap-3"
      >
        <h2 id="projects-heading" className="text-lg font-semibold">
          Projects
        </h2>
        <ul className="flex flex-col gap-2">
          {list.map((project) => (
            <li key={project.name}>
              <Link
                to={`/p/${project.name}`}
                className="flex items-center justify-between gap-4 rounded-lg border bg-surface px-4 py-3 outline-none hover:bg-surface-sunken focus-visible:ring-[3px] focus-visible:ring-accent/50"
              >
                <div className="flex min-w-0 flex-col gap-1.5">
                  <span className="truncate font-mono font-medium">
                    {project.name}
                  </span>
                  <ProgressLine done={project.done} total={project.total} />
                </div>
                <ProjectStatus project={project} />
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
