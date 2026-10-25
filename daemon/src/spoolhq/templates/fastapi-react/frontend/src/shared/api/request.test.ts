import { expect, it, vi } from "vitest";

import { ApiError, request } from "./request";

it("returns the parsed body", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(Response.json({ ok: true }));
  expect(await request("/x")).toEqual({ ok: true });
});

it("throws ApiError with the status and body", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response("missing", { status: 404 }),
  );
  const error = await request("/x").catch((reason: unknown) => reason);
  expect(error).toBeInstanceOf(ApiError);
  expect(error).toMatchObject({ status: 404, body: "missing" });
});
