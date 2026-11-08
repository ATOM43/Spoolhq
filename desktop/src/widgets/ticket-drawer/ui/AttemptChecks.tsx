import {
  CircleCheck,
  CircleDashed,
  CircleX,
  Eye,
  RotateCw,
  type LucideIcon,
} from "lucide-react";

import { useArtifact } from "@/entities/run";
import type { TicketAttempt } from "@/entities/ticket";
import { cn } from "@/shared/lib";
import { Button } from "@/shared/ui";

import { gatesLine, reviewLine, type CheckTone } from "../model/summary";

const LOOK: Record<CheckTone, { icon: LucideIcon; tone: string }> = {
  passed: { icon: CircleCheck, tone: "text-success" },
  failed: { icon: CircleX, tone: "text-danger" },
  waiting: { icon: Eye, tone: "text-warning" },
  none: { icon: CircleDashed, tone: "text-ink-muted" },
};

/** An attempt's gate and review summary, one line each (icon + text). */
export function AttemptChecks({
  project,
  attempt,
}: {
  project: string;
  attempt: TicketAttempt;
}) {
  const gates = useArtifact("gates", project, attempt.run_id, attempt.number);
  const review = useArtifact("review", project, attempt.run_id, attempt.number);
  if (gates.isPending || review.isPending) {
    return <p className="text-xs text-ink-muted">Loading the checks…</p>;
  }
  if (gates.isError || review.isError) {
    return (
      <div role="alert" className="flex items-center gap-2 text-xs">
        <span className="text-danger">
          Couldn't load the checks: {(gates.error ?? review.error)?.message}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            void gates.refetch();
            void review.refetch();
          }}
        >
          <RotateCw aria-hidden />
          Retry
        </Button>
      </div>
    );
  }
  return (
    <ul
      aria-label={`Attempt ${String(attempt.number)} checks`}
      className="flex flex-col gap-0.5 text-xs"
    >
      {[gatesLine(gates.data ?? null), reviewLine(review.data ?? null)].map(
        ({ tone, text }) => {
          const { icon: Icon, tone: colour } = LOOK[tone];
          return (
            <li key={text} className="flex items-center gap-1.5">
              <Icon aria-hidden className={cn("size-3.5 shrink-0", colour)} />
              {text}
            </li>
          );
        },
      )}
    </ul>
  );
}
