import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "@/shared/api";

import { NewTicketDrawer } from "./NewTicketDrawer";

vi.mock("@/shared/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/shared/api")>();
  return { ...actual, api: { GET: vi.fn(), POST: vi.fn() } };
});

type Handler = (path: string, init?: unknown) => unknown;
const GET = vi.mocked(api.GET) as unknown as ReturnType<typeof vi.fn<Handler>>;
const POST = vi.mocked(api.POST) as unknown as ReturnType<
  typeof vi.fn<Handler>
>;
const ok = (data: unknown) =>
  Promise.resolve({ data, response: new Response() });

const onSaved = vi.fn<(id: string) => void>();
const onClose = vi.fn<() => void>();

/** A planner draft, as T41 will hand it to the form. */
const DRAFT = {
  title: "Export as CSV",
  scope: "- An Export button on the table.",
  doneWhen: "- [ ] The file opens in a spreadsheet",
  dependsOn: ["T02"],
  estimate: "2.5",
  reviewRequired: true,
};

describe("New ticket drawer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    GET.mockImplementation(() =>
      ok({
        tickets: [{ id: "T02", meta: { id: "T02", title: "Table" } }],
        invalid: [],
      }),
    );
    POST.mockImplementation(() => ok({ id: "T03" }));
  });

  it("accepts pre-filled values, unsaved until Save", async () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <NewTicketDrawer
          project="demo"
          draft={DRAFT}
          onSaved={onSaved}
          onClose={onClose}
        />
      </QueryClientProvider>,
    );
    expect(screen.getByRole("textbox", { name: "Title" })).toHaveValue(
      "Export as CSV",
    );
    expect(screen.getByRole("textbox", { name: "Scope" })).toHaveValue(
      DRAFT.scope,
    );
    expect(screen.getByRole("spinbutton")).toHaveValue(2.5);
    expect(
      screen.getByRole("checkbox", { name: "Review required" }),
    ).toBeChecked();
    expect(await screen.findByRole("checkbox", { name: /T02/ })).toBeChecked();
    expect(POST).not.toHaveBeenCalled();

    // A filled draft is unsaved text: leaving asks first.
    await userEvent.keyboard("{Escape}");
    expect(onClose).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: "Keep going" }));

    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(POST).toHaveBeenCalledWith("/api/projects/{name}/tickets", {
      params: { path: { name: "demo" } },
      body: {
        title: "Export as CSV",
        scope: DRAFT.scope,
        done_when: DRAFT.doneWhen,
        depends_on: ["T02"],
        estimate_h: 2.5,
        review_required: true,
      },
    });
    await vi.waitFor(() => {
      expect(onSaved).toHaveBeenCalledWith("T03");
    });
  });
});
