import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Markdown } from "./markdown";

describe("Markdown", () => {
  it("renders untrusted HTML and javascript: links as inert", () => {
    const source = [
      "# Spec",
      "",
      "<script>window.pwned = true</script>",
      "",
      '<img src="x" onerror="window.pwned = true">',
      "",
      "[click me](javascript:alert(1)) and [docs](https://example.com)",
    ].join("\n");
    const { container } = render(<Markdown source={source} />);

    expect(screen.getByRole("heading", { name: "Spec" })).toBeInTheDocument();
    expect(container.querySelector("script")).toBeNull();
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("[onerror]")).toBeNull();
    const bad = screen.getByText("click me");
    expect(bad.getAttribute("href") ?? "").not.toMatch(/javascript/i);
    expect(screen.getByText("docs")).toHaveAttribute(
      "href",
      "https://example.com",
    );
    expect((window as { pwned?: boolean }).pwned).toBeUndefined();
    const click = new MouseEvent("click", { bubbles: true, cancelable: true });
    screen.getByText("docs").dispatchEvent(click);
    expect(click.defaultPrevented).toBe(true); // never navigates the webview
  });

  it("drops a javascript: image source too", () => {
    const { container } = render(
      <Markdown source="![x](javascript:alert(1))" />,
    );
    expect(container.querySelector("img")?.getAttribute("src") ?? "").toBe("");
  });

  it("renders task lists as disabled checkboxes, and tables", () => {
    const source = [
      "- [x] done",
      "- [ ] open",
      "",
      "| Item | State |",
      "| --- | --- |",
      "| T04 | met |",
    ].join("\n");
    render(<Markdown source={source} />);

    const boxes = screen.getAllByRole("checkbox");
    expect(boxes).toHaveLength(2);
    expect(boxes[0]).toBeChecked();
    expect(boxes[1]).not.toBeChecked();
    for (const box of boxes) {
      expect(box).toBeDisabled();
    }
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(
      screen.getByRole("columnheader", { name: "State" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "met" })).toBeInTheDocument();
  });

  it("keeps HTML and javascript: links inert inside GFM tables", () => {
    const source = [
      "| a | b |",
      "| --- | --- |",
      "| <script>window.pwned = true</script> | [x](javascript:alert(1)) |",
    ].join("\n");
    const { container } = render(<Markdown source={source} />);
    expect(container.querySelector("script")).toBeNull();
    expect(screen.getByText("x").getAttribute("href") ?? "").not.toMatch(
      /javascript/i,
    );
    expect((window as { pwned?: boolean }).pwned).toBeUndefined();
  });
});
