import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { DaemonError } from "@/shared/api";

import { DaemonDownPanel, DaemonErrorPanel } from "./DaemonPanel";

describe("DaemonDownPanel", () => {
  it("says the daemon isn't running and shows the command to start it", () => {
    render(<DaemonDownPanel port={8765} onRetry={vi.fn()} checking={false} />);
    expect(
      screen.getByRole("heading", { name: "The daemon isn't running" }),
    ).toBeInTheDocument();
    expect(screen.getByText("spool serve")).toBeInTheDocument();
    expect(screen.getByText(/127\.0\.0\.1:8765/)).toBeInTheDocument();
  });

  it("retries when Retry is clicked", async () => {
    const onRetry = vi.fn();
    render(<DaemonDownPanel port={8765} onRetry={onRetry} checking={false} />);
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("copies the command", async () => {
    const user = userEvent.setup();
    render(<DaemonDownPanel port={8765} onRetry={vi.fn()} checking={false} />);
    await user.click(screen.getByRole("button", { name: "Copy spool serve" }));
    await expect(navigator.clipboard.readText()).resolves.toBe("spool serve");
    expect(screen.getByText("Copied")).toBeInTheDocument();
  });
});

describe("DaemonErrorPanel", () => {
  it("names the token file when the token is missing", () => {
    const error = new DaemonError({
      kind: "token_missing",
      tokenPath: "/home/me/.spoolhq/token",
    });
    render(
      <DaemonErrorPanel error={error} onRetry={vi.fn()} checking={false} />,
    );
    expect(
      screen.getByText(/\/home\/me\/\.spoolhq\/token/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
