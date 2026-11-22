import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { DaemonError } from "@/shared/api";

import {
  DaemonDownPanel,
  DaemonErrorPanel,
  DaemonStatusPanel,
} from "./DaemonPanel";

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

describe("DaemonStatusPanel", () => {
  it("says SpoolHQ is starting while the app starts its daemon", () => {
    render(
      <DaemonStatusPanel
        status={{ state: "starting" }}
        onRetry={vi.fn()}
        checking={false}
      />,
    );
    expect(screen.getByText("Starting SpoolHQ…")).toBeInTheDocument();
  });

  it("names the busy port and how to change it", () => {
    render(
      <DaemonStatusPanel
        status={{
          state: "port_in_use",
          port: 8765,
          configPath: "/home/me/.spoolhq/config.toml",
        }}
        onRetry={vi.fn()}
        checking={false}
      />,
    );
    expect(
      screen.getByRole("heading", {
        name: "Port 8765 is used by another program",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /set port = 8766 in \/home\/me\/\.spoolhq\/config\.toml \(or the SPOOLHQ_PORT/,
      ),
    ).toBeInTheDocument();
  });

  it("shows the log folder when the app's daemon did not answer", () => {
    render(
      <DaemonStatusPanel
        status={{ state: "down", port: 8765, logDir: "/home/me/.spoolhq/logs" }}
        onRetry={vi.fn()}
        checking={false}
      />,
    );
    expect(
      screen.getByRole("heading", { name: "The daemon isn't running" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/its logs are in \/home\/me\/\.spoolhq\/logs/),
    ).toBeInTheDocument();
  });
});
