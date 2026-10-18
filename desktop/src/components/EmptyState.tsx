import type { ReactNode } from "react";

/** A centred placeholder for screens that have no content yet. */
export function EmptyState({
  icon,
  title,
  description,
}: {
  icon: ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed bg-surface-sunken px-6 py-12 text-center">
      <div className="text-ink-muted [&_svg]:size-6">{icon}</div>
      <p className="font-medium">{title}</p>
      <p className="max-w-md text-sm text-ink-muted">{description}</p>
    </div>
  );
}
