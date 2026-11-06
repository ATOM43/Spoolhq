// shadcn/ui Textarea (new-york-v4), restyled with SpoolHQ tokens.
import type * as React from "react";

import { cn } from "@/shared/lib";

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "flex min-h-20 w-full rounded-md border bg-surface px-3 py-2 text-sm text-ink shadow-xs outline-none placeholder:text-ink-muted focus-visible:ring-[3px] focus-visible:ring-accent/50 disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-danger aria-invalid:ring-danger/20",
        className,
      )}
      {...props}
    />
  );
}

export { Textarea };
