import { expect, it, vi } from "vitest";

import { getItem, listItems } from "./items";

it("lists items", async () => {
  const fetchMock = vi
    .spyOn(globalThis, "fetch")
    .mockResolvedValue(Response.json([{ id: 1, name: "a", description: "" }]));
  expect(await listItems()).toEqual([{ id: 1, name: "a", description: "" }]);
  expect(fetchMock).toHaveBeenCalledWith("/api/items", undefined);
});

it("gets one item", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    Response.json({ id: 3, name: "c", description: "" }),
  );
  expect(await getItem(3)).toEqual({ id: 3, name: "c", description: "" });
});
