import { cn } from "@/shared/lib";

/**
 * A ticket id as a monospace chip that opens the ticket. `met` styles a dependency:
 * solid when it is done, outlined while it isn't.
 */
export function TicketChip({
  id,
  onOpen,
  met,
  label,
}: {
  id: string;
  onOpen: (id: string) => void;
  met?: boolean | undefined;
  /** The accessible name, when the id alone doesn't say enough. */
  label?: string | undefined;
}) {
  return (
    <button
      type="button"
      aria-label={label ?? `Open ${id}`}
      data-met={met === undefined ? undefined : String(met)}
      onClick={(event) => {
        event.stopPropagation(); // inside a row that opens its own ticket
        onOpen(id);
      }}
      className={cn(
        "rounded-sm border px-1.5 py-0.5 font-mono text-xs outline-none hover:border-accent focus-visible:ring-[3px] focus-visible:ring-accent/50",
        met === false
          ? "border-ink-muted/60 bg-transparent"
          : "border-transparent bg-surface-sunken",
      )}
    >
      {id}
    </button>
  );
}
