/** A full-width bar over "13 of 18 done · 12 h left"; a native <progress>, so no
 * inline styles. */
export function ProgressLine({
  done,
  total,
  remainingH = 0,
}: {
  done: number;
  total: number;
  remainingH?: number;
}) {
  const label =
    total === 0
      ? "No tickets yet"
      : [
          `${String(done)} of ${String(total)} done`,
          remainingH > 0 ? `${String(remainingH)} h left` : null,
        ]
          .filter(Boolean)
          .join(" · ");
  return (
    <div className="flex flex-col gap-1.5">
      <progress
        value={done}
        max={Math.max(total, 1)}
        aria-label={`${String(done)} of ${String(total)} tickets done`}
        className="h-1 w-full overflow-hidden rounded-full bg-surface-sunken [&::-moz-progress-bar]:bg-accent [&::-webkit-progress-bar]:bg-surface-sunken [&::-webkit-progress-value]:bg-accent"
      />
      <span className="text-sm text-ink-muted">{label}</span>
    </div>
  );
}
