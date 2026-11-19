import { CircleCheck, Info, TriangleAlert } from "lucide-react";

import type { Inspection } from "../model/api";
import { DIRTY_REASON } from "../model/form";

/** Under the repo folder, for an existing repo: its state, its own agent settings, and
 * Graphify when it isn't installed. */
export function RepoNotices({
  found,
  graphify,
}: {
  found: Inspection;
  graphify: boolean | undefined;
}) {
  return (
    <section
      aria-label="Repository"
      className="-mt-2 flex flex-col gap-2 text-sm [&_svg]:size-4 [&_svg]:shrink-0"
    >
      {found.clean ? (
        <p className="flex items-center gap-2 text-success">
          <CircleCheck aria-hidden />
          Clean · on {found.branch}
        </p>
      ) : (
        <div role="alert" className="rounded-lg border border-warning/40 p-3">
          <p className="flex items-center gap-2 text-warning">
            <TriangleAlert aria-hidden />
            Uncommitted changes on {found.branch} · {DIRTY_REASON}
          </p>
          <ul className="mt-2 ml-6 max-h-32 overflow-auto font-mono text-xs">
            {found.dirty.map((entry) => (
              <li key={entry} className="whitespace-pre">
                {entry}
              </li>
            ))}
          </ul>
        </div>
      )}
      {found.agent_settings.length > 0 ? (
        <p className="flex items-start gap-2">
          <Info aria-hidden className="mt-0.5 text-accent" />
          <span>
            This repo has its own agent settings (
            {found.agent_settings.join(", ")}). SpoolHQ ignores them during
            runs.
          </span>
        </p>
      ) : null}
      {graphify === false ? (
        <p className="text-ink-muted">
          Recommended for existing repos: install Graphify so the agent can find
          its way around.
        </p>
      ) : null}
    </section>
  );
}
