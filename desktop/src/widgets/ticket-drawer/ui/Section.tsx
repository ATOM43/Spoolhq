import type { ReactNode } from "react";

/** One titled section of the drawer's scrolling column. */
export function Section({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section aria-label={title} className="flex flex-col gap-2">
      <h3 className="text-xs font-semibold tracking-wide text-ink-muted uppercase">
        {title}
      </h3>
      {children}
    </section>
  );
}
