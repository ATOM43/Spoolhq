/** "182k tokens", "1.2M tokens". */
export function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) {
    return `${(tokens / 1_000_000).toFixed(1)}M tokens`;
  }
  return tokens >= 1000
    ? `${String(Math.round(tokens / 1000))}k tokens`
    : `${String(tokens)} tokens`;
}

/** USD for API-key backends, tokens for subscriptions, both when a project mixes them
 * ("$0.84 · 182k tokens"); null when nothing was used. */
export function formatUsage(
  tokens: number,
  usd: number | null | undefined,
): string | null {
  const parts = [
    usd == null ? null : `$${usd.toFixed(2)}`,
    tokens > 0 ? formatTokens(tokens) : null,
  ].filter((part) => part !== null);
  return parts.length > 0 ? parts.join(" · ") : null;
}

/** "just now", "12 min ago", "3 h ago", "2 d ago". */
export function timeAgo(iso: string, now: number = Date.now()): string {
  const minutes = Math.floor((now - new Date(iso).getTime()) / 60_000);
  if (minutes < 1) {
    return "just now";
  }
  if (minutes < 60) {
    return `${String(minutes)} min ago`;
  }
  const hours = Math.floor(minutes / 60);
  return hours < 24
    ? `${String(hours)} h ago`
    : `${String(Math.floor(hours / 24))} d ago`;
}

/** The local date and time, for the hover text of a relative time. */
export const formatTime = (iso: string): string =>
  new Date(iso).toLocaleString();
