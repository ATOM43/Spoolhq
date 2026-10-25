import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";

import { ItemsPanel } from "./ItemsPanel";

it("lists the items and adds a created one", async () => {
  const fetchMock = vi
    .spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(
      Response.json([{ id: 1, name: "First", description: "" }]),
    )
    .mockResolvedValueOnce(
      Response.json(
        { id: 2, name: "Second", description: "" },
        { status: 201 },
      ),
    );
  render(<ItemsPanel />);
  expect(await screen.findByText("First")).toBeInTheDocument();

  await userEvent.type(screen.getByLabelText("Name"), "Second");
  await userEvent.click(screen.getByRole("button", { name: "Add" }));

  expect(await screen.findByText("Second")).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledTimes(2);
});

it("shows a failed load", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response("boom", { status: 500 }),
  );
  render(<ItemsPanel />);
  expect(await screen.findByRole("alert")).toHaveTextContent("500");
});
