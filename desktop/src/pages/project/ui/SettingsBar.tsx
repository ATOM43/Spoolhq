import { CircleX, RotateCw } from "lucide-react";

import { settingsErrorLine, type ProjectDetail } from "@/entities/project";
import { Button, CopyButton } from "@/shared/ui";

/** The red bar under the header while `project.yaml` doesn't load. */
export function SettingsBar({
  project,
  reloading,
  onReload,
}: {
  project: ProjectDetail;
  reloading: boolean;
  onReload: () => void;
}) {
  const problem = project.settings_error;
  if (!problem) {
    return null;
  }
  return (
    <div
      role="alert"
      className="flex flex-wrap items-center gap-x-3 gap-y-1 bg-danger/10 px-6 py-2 text-sm"
    >
      <CircleX aria-hidden className="size-4 shrink-0 text-danger" />
      <span className="font-medium text-danger">
        {settingsErrorLine(project)}
      </span>
      <span className="flex min-w-0 items-center gap-1 text-ink-muted">
        <code className="truncate font-mono text-xs">{problem.file}</code>
        <CopyButton text={problem.file} label="Copy settings file path" />
      </span>
      <Button
        variant="outline"
        size="sm"
        className="ml-auto"
        disabled={reloading}
        onClick={onReload}
      >
        <RotateCw aria-hidden className={reloading ? "animate-spin" : ""} />
        Reload
      </Button>
    </div>
  );
}
