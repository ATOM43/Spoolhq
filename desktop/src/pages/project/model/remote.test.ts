import { describe, expect, it } from "vitest";

import { remoteHost } from "./remote";

describe("remoteHost", () => {
  it("reads the host of https and ssh remotes", () => {
    expect(remoteHost("https://github.com/a/b.git")).toBe("github.com");
    expect(remoteHost("git@gitlab.example.com:a/b.git")).toBe(
      "gitlab.example.com",
    );
    expect(remoteHost("origin")).toBe("origin");
  });
});
