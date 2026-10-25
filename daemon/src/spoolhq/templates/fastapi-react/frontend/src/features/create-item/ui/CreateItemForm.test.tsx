import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";

import { CreateItemForm } from "./CreateItemForm";

it("creates an item and clears the field", async () => {
  const fetchMock = vi
    .spyOn(globalThis, "fetch")
    .mockResolvedValue(
      Response.json({ id: 7, name: "Spool", description: "" }, { status: 201 }),
    );
  const onCreated = vi.fn();
  render(<CreateItemForm onCreated={onCreated} />);

  const field = screen.getByLabelText("Name");
  expect(screen.getByRole("button", { name: "Add" })).toBeDisabled();
  await userEvent.type(field, " Spool ");
  await userEvent.click(screen.getByRole("button", { name: "Add" }));

  expect(onCreated).toHaveBeenCalledWith({
    id: 7,
    name: "Spool",
    description: "",
  });
  expect(field).toHaveValue("");
  const [, init] = fetchMock.mock.calls[0] ?? [];
  expect(init?.body).toBe(JSON.stringify({ name: "Spool" }));
});

it("shows the error when the API refuses", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response("nope", { status: 422 }),
  );
  render(<CreateItemForm onCreated={vi.fn()} />);
  await userEvent.type(screen.getByLabelText("Name"), "x");
  await userEvent.click(screen.getByRole("button", { name: "Add" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("422");
});
