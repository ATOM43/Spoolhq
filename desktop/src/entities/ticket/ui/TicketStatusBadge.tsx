import { cn } from "@/shared/lib";

import type { TicketStatus } from "../model/queries";
import { STATUS_LOOK } from "./status-look";

export function TicketStatusBadge({ status }: { status: TicketStatus }) {
  const { icon, tone, label } = STATUS_LOOK[status];
  return (
    <span
      data-status={status}
      className={cn(
        "inline-flex items-center gap-1.5 text-sm whitespace-nowrap [&_svg]:size-3.5",
        tone,
      )}
    >
      {icon}
      {label}
    </span>
  );
}
