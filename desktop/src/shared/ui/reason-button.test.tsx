import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ReasonButton } from "./reason-button";

describe("ReasonButton", () => {
  it("is a plain primary button without a reason", () => {
    render(<ReasonButton>Run next</ReasonButton>);
    const button = screen.getByRole("button", { name: "Run next" });
    expect(button).toBeEnabled();
    expect(button).toHaveClass("bg-accent");
    expect(screen.queryByRole("tooltip", { hidden: true })).toBeNull();
  });

  it("looks disabled, never in the accent colour, and says why", () => {
    render(
      <ReasonButton reason="Approve the plan first">Run next</ReasonButton>,
    );
    const button = screen.getByRole("button", { name: "Run next" });
    expect(button).toBeDisabled();
    expect(button).toHaveClass("text-ink-muted");
    expect(button).not.toHaveClass("bg-accent");
    expect(button).toHaveAccessibleDescription("Approve the plan first");
    expect(button.parentElement).toHaveAttribute(
      "title",
      "Approve the plan first",
    );
  });

  it("shows the reason on hover and on keyboard focus, with CSS only", async () => {
    render(
      <ReasonButton reason="Approve the plan first">Run next</ReasonButton>,
    );
    const tip = screen.getByRole("tooltip", { hidden: true });
    expect(tip).toHaveTextContent("Approve the plan first");
    // Hidden until the wrapper is hovered or focused: Tailwind group variants.
    expect(tip).toHaveClass(
      "hidden",
      "group-hover:block",
      "group-focus-visible:block",
    );
    expect(tip).not.toHaveAttribute("style");

    await userEvent.tab();
    const wrapper = tip.parentElement;
    expect(wrapper).toHaveFocus();
    expect(wrapper).toHaveClass("group");
    expect(wrapper).toHaveAttribute("aria-describedby", tip.id);
  });
});
