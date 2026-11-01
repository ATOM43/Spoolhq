// shadcn/ui Input (new-york-v4), restyled with SpoolHQ tokens.
import type * as React from "react";

import { cn } from "@/shared/lib";

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "flex h-9 w-full min-w-0 rounded-md border bg-surface px-3 py-1 text-sm text-ink shadow-xs outline-none placeholder:text-ink-muted focus-visible:ring-[3px] focus-visible:ring-accent/50 disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-danger aria-invalid:ring-danger/20",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
