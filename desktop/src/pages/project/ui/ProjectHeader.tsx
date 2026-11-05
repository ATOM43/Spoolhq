import { Folder, GitBranch, House } from "lucide-react";
import { Link } from "react-router";

import type { ProjectDetail } from "@/entities/project";
import { SettingsDialog } from "@/features/settings";
import { CopyButton } from "@/shared/ui";

import { remoteHost } from "../model/remote";

/** V2 header, row 1: breadcrumb, repo path with copy, branch and remote; Settings at
 * the right end, always enabled (also with an invalid project.yaml). */
export function ProjectHeader({ project }: { project: ProjectDetail }) {
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-x-4 gap-y-1 text-sm">
      <nav aria-label="Breadcrumb" className="flex items-center gap-2">
        <Link
          to="/"
          className="flex items-center gap-1 text-accent hover:underline"
        >
          <House aria-hidden className="size-4" />
          Home
        </Link>
        <span aria-hidden className="text-ink-muted">
          /
        </span>
        <h1 className="text-xl font-semibold tracking-tight">{project.name}</h1>
      </nav>
      {project.repo ? (
        <span className="flex min-w-0 items-center gap-1 text-ink-muted">
          <Folder aria-hidden className="size-4 shrink-0" />
          <code className="truncate font-mono text-xs">{project.repo}</code>
          <CopyButton text={project.repo} label="Copy repository path" />
        </span>
      ) : null}
      {project.default_branch ? (
        <span className="flex items-center gap-1 text-ink-muted">
          <GitBranch aria-hidden className="size-4" />
          <code className="font-mono text-xs">{project.default_branch}</code>
        </span>
      ) : null}
      {project.repo ? (
        <span className="text-ink-muted">
          {project.remote
            ? remoteHost(project.remote)
            : "Local git · no remote"}
        </span>
      ) : null}
      <div className="ml-auto">
        <SettingsDialog icon />
      </div>
    </div>
  );
}
