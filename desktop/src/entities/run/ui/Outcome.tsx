import {
  CircleAlert,
  CircleCheck,
  CirclePause,
  CircleSlash,
  CircleX,
  Eye,
  type LucideIcon,
} from "lucide-react";

const ICONS: Record<string, { icon: LucideIcon; tone: string }> = {
  done: { icon: CircleCheck, tone: "text-success" },
  approved: { icon: CircleCheck, tone: "text-success" },
  blocked: { icon: CircleX, tone: "text-danger" },
  gates_failed: { icon: CircleX, tone: "text-danger" },
  error: { icon: CircleX, tone: "text-danger" },
  awaiting_approval: { icon: Eye, tone: "text-warning" },
  needs_human: { icon: Eye, tone: "text-warning" },
  paused: { icon: CirclePause, tone: "text-warning" },
  cancelled: { icon: CircleSlash, tone: "text-ink-muted" },
};

/** A run's or an attempt's outcome: always an icon and its label. */
export function Outcome({ status, label }: { status: string; label: string }) {
  const { icon: Icon, tone } = ICONS[status] ?? {
    icon: CircleAlert,
    tone: "text-warning",
  };
  return (
    <span className={`flex items-center gap-1 text-sm font-medium ${tone}`}>
      <Icon aria-hidden className="size-4" />
      {label}
    </span>
  );
}
