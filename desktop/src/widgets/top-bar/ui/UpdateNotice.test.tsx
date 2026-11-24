import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { openSettings } from "@/features/settings";
import { getUpdateStatus, type UpdateCheck } from "@/shared/api";

import { UpdateNotice } from "./UpdateNotice";

vi.mock("@/shared/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/shared/api")>()),
  getUpdateStatus: vi.fn(),
}));
vi.mock("@/features/settings", () => ({ openSettings: vi.fn() }));

function renderNotice(check: UpdateCheck) {
  vi.mocked(getUpdateStatus).mockResolvedValue({
    current_version: "0.1.0",
    check,
    install: "in_place",
    external_daemon: false,
    installing: false,
    install_error: null,
  });
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <UpdateNotice />
    </QueryClientProvider>,
  );
}

describe("UpdateNotice", () => {
  it("shows the new version as icon + label and opens Settings → About", async () => {
    const { container } = renderNotice({
      state: "available",
      version: "0.2.0",
      notes: "",
      minimum_version: null,
      checked_at: 0,
    });
    const notice = await screen.findByRole("button", {
      name: "Update available · v0.2.0",
    });
    expect(container.querySelector("svg")).not.toBeNull();
    await userEvent.click(notice);
    expect(openSettings).toHaveBeenCalledWith("about");
  });

  it("shows nothing when up to date or after a failed check", async () => {
    for (const check of [
      { state: "up_to_date", checked_at: 0 },
      { state: "failed", checked_at: 0 },
    ] as const) {
      const { container, unmount } = renderNotice(check);
      await new Promise((resolve) => setTimeout(resolve, 0));
      expect(container).toBeEmptyDOMElement();
      unmount();
    }
  });
});
