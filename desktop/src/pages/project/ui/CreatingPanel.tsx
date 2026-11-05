import { FolderX } from "lucide-react";
import { useEffect } from "react";
import { Link } from "react-router";

import { ProjectStatus, type ProjectDetail } from "@/entities/project";
import { Checklist, useJob } from "@/features/project-create";
import { Button, EmptyState } from "@/shared/ui";

import { ProjectHeader } from "./ProjectHeader";

/** A project a creation job still holds: the header says "Creating…" and the tab area
 * shows the job's live checklist; nothing else is read until the job ends. */
export function CreatingPanel({
  project,
  job: id,
  onCreated,
}: {
  project: ProjectDetail;
  job: string;
  onCreated: () => void;
}) {
  const job = useJob(id).data;
  const state = job?.state;
  useEffect(() => {
    if (state === "succeeded") {
      onCreated();
    }
  }, [state, onCreated]);

  if (state === "failed" || state === "cancelled") {
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-6 py-6">
        <EmptyState
          icon={<FolderX aria-hidden />}
          title="This project wasn't created"
          description={
            state === "cancelled"
              ? "Its creation was cancelled and rolled back."
              : "A step failed and what was created was rolled back."
          }
          action={
            <Button asChild>
              <Link to="/">Back to Home</Link>
            </Button>
          }
        />
        {job ? <Checklist job={job} /> : null}
      </div>
    );
  }
  return (
    <>
      <div className="flex flex-col gap-2 px-6 pt-4 pb-2">
        <ProjectHeader project={project} />
        <div className="pt-2 text-sm">
          <ProjectStatus project={project} />
        </div>
      </div>
      <div className="border-t p-6">{job ? <Checklist job={job} /> : null}</div>
    </>
  );
}
