import { CircleX, LoaderCircle, RotateCw, Sparkles } from "lucide-react";
import { useState } from "react";

import type { ProjectDetail } from "@/entities/project";
import { OpenSettingsLink } from "@/features/settings";
import { Button, ConfirmDialog, ReasonButton } from "@/shared/ui";

import type { PlanState } from "../model/plan";

/** Generate plan / Re-plan, the planner's progress while it runs, and its failure. */
export function PlanButton({
  project,
  plan,
  blocker,
  pending,
  onGenerate,
  onViewPlan,
}: {
  project: ProjectDetail;
  plan: PlanState;
  blocker: string | null;
  pending: boolean;
  onGenerate: () => void;
  onViewPlan: () => void;
}) {
  const [confirming, setConfirming] = useState(false);
  const replan = project.total > 0;

  if (plan.planning) {
    return (
      <span className="flex items-center gap-2 text-sm">
        <LoaderCircle aria-hidden className="size-4 animate-spin text-accent" />
        Planning…
        <Button variant="link" size="sm" onClick={onViewPlan}>
          View
        </Button>
      </span>
    );
  }
  return (
    <>
      <ReasonButton
        reason={pending ? "Starting the planner…" : blocker}
        variant={replan ? "outline" : "default"}
        onClick={() => {
          if (replan) {
            setConfirming(true);
          } else {
            onGenerate();
          }
        }}
      >
        <Sparkles aria-hidden />
        {replan ? "Re-plan" : "Generate plan"}
      </ReasonButton>
      <OpenSettingsLink reason={pending ? null : blocker} />
      <ConfirmDialog
        open={confirming}
        title="Re-plan from the spec?"
        consequence="The planner drafts tickets again. Draft tickets you haven't edited are replaced; edited and approved tickets are kept."
        action="Re-plan"
        onCancel={() => {
          setConfirming(false);
        }}
        onConfirm={() => {
          setConfirming(false);
          onGenerate();
        }}
      />
    </>
  );
}

/** The red bar under the toolbar when planning failed or couldn't start. */
export function PlanFailure({
  reason,
  blocker,
  onRetry,
}: {
  reason: string;
  blocker: string | null;
  onRetry: () => void;
}) {
  return (
    <div
      role="alert"
      className="flex items-center gap-2 rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm"
    >
      <CircleX aria-hidden className="size-4 shrink-0 text-danger" />
      <span className="flex-1">Planning failed: {reason}</span>
      <ReasonButton
        variant="outline"
        size="sm"
        reason={blocker}
        onClick={onRetry}
      >
        <RotateCw aria-hidden />
        Retry
      </ReasonButton>
      <OpenSettingsLink reason={blocker} />
    </div>
  );
}
