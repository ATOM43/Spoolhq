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
});
