/** "3 of 10 tickets done" with a bar; a native <progress>, so no inline styles. */
export function ProgressLine({ done, total }: { done: number; total: number }) {
  const label =
    total === 0
      ? "No tickets yet"
      : `${String(done)} of ${String(total)} tickets done`;
  return (
    <div className="flex items-center gap-3">
      <progress
        value={done}
        max={Math.max(total, 1)}
        aria-label={label}
        className="h-1.5 w-32 overflow-hidden rounded-full bg-surface-sunken [&::-moz-progress-bar]:bg-accent [&::-webkit-progress-bar]:bg-surface-sunken [&::-webkit-progress-value]:bg-accent"
      />
      <span className="text-sm text-ink-muted">{label}</span>
    </div>
  );
}
