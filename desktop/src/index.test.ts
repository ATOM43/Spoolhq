import { describe, expect, it } from "vitest";

import { appName } from "./index.js";

describe("appName", () => {
  it("returns the product name", () => {
    expect(appName()).toBe("SpoolHQ");
  });
});
