import {
  Circle,
  CircleCheck,
  CircleDashed,
  Eye,
  LoaderCircle,
  OctagonX,
} from "lucide-react";
import type { ReactNode } from "react";

import type { TicketStatus } from "../model/queries";

/** The screens spec's status table: icon, colour and label, never colour alone. */
export const STATUS_LOOK: Record<
  TicketStatus,
  { icon: ReactNode; tone: string; label: string }
> = {
  draft: {
    icon: <CircleDashed aria-hidden />,
    tone: "text-ink-muted",
    label: "Draft",
  },
  ready: { icon: <Circle aria-hidden />, tone: "text-ink", label: "Ready" },
  running: {
    icon: <LoaderCircle aria-hidden className="animate-spin" />,
    tone: "text-accent",
    label: "Running",
  },
  awaiting_approval: {
    icon: <Eye aria-hidden />,
    tone: "text-warning",
    label: "Needs approval",
  },
  blocked: {
    icon: <OctagonX aria-hidden />,
    tone: "text-danger",
    label: "Blocked",
  },
  done: {
    icon: <CircleCheck aria-hidden />,
    tone: "text-success",
    label: "Done",
  },
};
