import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DaemonError } from "@/shared/api";

import { StatusPill } from "./StatusPill";

describe("StatusPill", () => {
  it("shows ok with the daemon's version", () => {
    render(
      <StatusPill status={{ state: "ok", version: "0.1.0", port: 8765 }} />,
    );
    expect(screen.getByRole("status")).toHaveTextContent("Daemon ok · v0.1.0");
  });

  it("shows reconnecting", () => {
    render(<StatusPill status={{ state: "reconnecting" }} />);
    expect(screen.getByRole("status")).toHaveTextContent("Reconnecting…");
  });

  it("shows not running", () => {
    render(<StatusPill status={{ state: "down", port: 8765 }} />);
    expect(screen.getByRole("status")).toHaveTextContent("Daemon not running");
  });

  it("shows other failures as a daemon error", () => {
    const error = new DaemonError({ kind: "unauthorized" });
    render(<StatusPill status={{ state: "error", error }} />);
    expect(screen.getByRole("status")).toHaveTextContent("Daemon error");
  });

  it("always pairs the label with an icon", () => {
    const { container } = render(
      <StatusPill status={{ state: "down", port: null }} />,
    );
    expect(container.querySelector("svg")).not.toBeNull();
  });
});
