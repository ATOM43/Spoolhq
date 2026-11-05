import { describe, expect, it } from "vitest";

import { formatTokens, formatUsage, timeAgo } from "./format";

describe("format", () => {
  it("formats tokens by size", () => {
    expect(formatTokens(950)).toBe("950 tokens");
    expect(formatTokens(182_400)).toBe("182k tokens");
    expect(formatTokens(1_230_000)).toBe("1.2M tokens");
  });

  it("shows USD, tokens or both", () => {
    expect(formatUsage(0, null)).toBeNull();
    expect(formatUsage(0, 9.852)).toBe("$9.85");
    expect(formatUsage(182_000, null)).toBe("182k tokens");
    expect(formatUsage(182_000, 0.84)).toBe("$0.84 · 182k tokens");
  });

  it("says how long ago", () => {
    const now = Date.parse("2026-11-05T12:00:00Z");
    expect(timeAgo("2026-11-05T11:59:40Z", now)).toBe("just now");
    expect(timeAgo("2026-11-05T11:48:00Z", now)).toBe("12 min ago");
    expect(timeAgo("2026-11-05T09:00:00Z", now)).toBe("3 h ago");
    expect(timeAgo("2026-11-03T12:00:00Z", now)).toBe("2 d ago");
  });
});
