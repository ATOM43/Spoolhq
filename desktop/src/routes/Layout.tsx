import { Outlet } from "react-router";

import { TopBar } from "@/components/TopBar";

export function Layout() {
  return (
    <div className="flex h-full flex-col">
      <TopBar />
      <main className="flex-1 overflow-auto bg-surface-sunken">
        <Outlet />
      </main>
    </div>
  );
}
