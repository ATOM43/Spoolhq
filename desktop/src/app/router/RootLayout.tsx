import { Outlet } from "react-router";

import { Toaster } from "@/shared/ui";

export function RootLayout() {
  return (
    <main className="h-full min-h-0 overflow-auto bg-surface">
      <Outlet />
      <Toaster />
    </main>
  );
}
