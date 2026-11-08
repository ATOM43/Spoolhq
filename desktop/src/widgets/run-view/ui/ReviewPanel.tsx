import {
  CircleCheck,
  CircleX,
  Eye,
  OctagonX,
  type LucideIcon,
} from "lucide-react";

import type { ReviewReport } from "@/entities/run";
import { cn } from "@/shared/lib";
import { Markdown } from "@/shared/ui";

import { Note } from "./Note";

const VERDICT: Record<
  NonNullable<ReviewReport["verdict"]>,
  { icon: LucideIcon; tone: string; label: string }
> = {
  approve: { icon: CircleCheck, tone: "text-success", label: "Approved" },
  changes_requested: {
    icon: CircleX,
    tone: "text-danger",
    label: "Changes requested",
  },
  needs_human: { icon: Eye, tone: "text-warning", label: "Needs a person" },
};

/** The verdict and summary, then each "Done when" item met or not, with the
 * reviewer's reason through the safe Markdown (untrusted text, never HTML). */
export function ReviewPanel({
  report,
  reviewing,
  ended,
}: {
  report: ReviewReport | null;
  reviewing: boolean;
  ended: boolean;
}) {
  if (report === null) {
    if (reviewing) {
      return <Note busy>Reviewing…</Note>;
    }
    return (
      <Note>
        {ended
          ? "No review in this attempt."
          : "The reviewer checks the diff after the gates pass."}
      </Note>
    );
  }
  if (report.verdict == null) {
    return (
      <Note>
        The reviewer stopped early (
        {(report.stopped ?? "error").replace("_", " ")}) without a verdict.
      </Note>
    );
  }
  const { icon: Icon, tone, label } = VERDICT[report.verdict];
  const met = report.items.filter((item) => item.met).length;
  return (
    <div className="flex flex-col gap-3">
      <p className={cn("flex items-center gap-2 font-semibold", tone)}>
        <Icon aria-hidden className="size-5" />
        {label}
        <span className="text-sm font-normal text-ink-muted">
          · {met} of {report.items.length} met
        </span>
      </p>
      {report.summary ? <Markdown source={report.summary} /> : null}
      <ul
        aria-label="Done when"
        className="flex flex-col divide-y rounded-md border"
      >
        {report.items.map((item, index) => (
          // Items are in the ticket's order and never reorder.
          <li key={index} className="flex gap-2 px-3 py-2 text-sm">
            {item.met ? (
              <CircleCheck
                aria-hidden
                className="mt-0.5 size-4 shrink-0 text-success"
              />
            ) : (
              <OctagonX
                aria-hidden
                className="mt-0.5 size-4 shrink-0 text-danger"
              />
            )}
            <div className="flex min-w-0 flex-col gap-1">
              <p className="font-medium">
                <span className="sr-only">
                  {item.met ? "Met: " : "Not met: "}
                </span>
                {item.text}
              </p>
              <div className="text-ink-muted">
                <Markdown source={item.reason} />
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
