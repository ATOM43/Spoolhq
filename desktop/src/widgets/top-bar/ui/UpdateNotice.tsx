import { CircleArrowUp } from "lucide-react";

import { useUpdateStatus } from "@/entities/update";
import { openSettings } from "@/features/settings";

/** "Update available · v0.2.0" (icon + label), opening Settings → About. */
export function UpdateNotice() {
  const check = useUpdateStatus().data?.check;
  if (check?.state !== "available") {
    return null;
  }
  return (
    <button
      type="button"
      onClick={() => {
        openSettings("about");
      }}
      className="inline-flex items-center gap-2 rounded-lg border border-accent/40 bg-accent/10 px-3 py-1 text-sm text-accent hover:bg-accent/20"
    >
      <CircleArrowUp aria-hidden className="size-4" />
      <span className="text-ink">Update available · v{check.version}</span>
    </button>
  );
}
