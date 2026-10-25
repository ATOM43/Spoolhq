import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import { App } from "./App";

it("renders the home page", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(Response.json([]));
  render(<App />);
  expect(screen.getByRole("heading", { name: "Items" })).toBeInTheDocument();
  expect(await screen.findByText("No items yet.")).toBeInTheDocument();
});
