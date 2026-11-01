import { ArrowLeft, GitBranch } from "lucide-react";
import { Link } from "react-router";

import type { ProjectDetail } from "@/entities/project";
import { CopyCommand } from "@/shared/ui";

/** V2 header, row 1 and the progress line. */
export function ProjectHeader({
  project,
  usage,
}: {
  project: ProjectDetail;
  usage: string | null;
}) {
  const progress = [
    `${String(project.done)} of ${String(project.total)} done`,
    project.remaining_h > 0 ? `${String(project.remaining_h)} h left` : null,
    usage ? `${usage} (latest run)` : null,
  ].filter(Boolean);
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <Link
          to="/"
          className="flex items-center gap-1 text-sm text-ink-muted hover:text-ink"
        >
          <ArrowLeft aria-hidden className="size-4" />
          Home
        </Link>
        <h1 className="text-xl font-semibold tracking-tight">{project.name}</h1>
        <div className="min-w-0 max-w-md flex-1">
          <CopyCommand command={project.repo} />
        </div>
        <span className="flex items-center gap-1 font-mono text-sm text-ink-muted">
          <GitBranch aria-hidden className="size-4" />
          {project.default_branch}
        </span>
        {project.remote ? (
          <span className="truncate font-mono text-sm text-ink-muted">
            GitHub: {project.remote}
          </span>
        ) : null}
      </div>
      <p className="text-sm text-ink-muted">{progress.join(" · ")}</p>
    </div>
  );
}
