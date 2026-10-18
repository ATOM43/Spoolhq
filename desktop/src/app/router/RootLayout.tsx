import { Outlet } from "react-router";

import { TopBar } from "@/widgets/top-bar";

export function RootLayout() {
  return (
    <div className="flex h-full flex-col">
      <TopBar />
      <main className="flex-1 overflow-auto bg-surface-sunken">
        <Outlet />
      </main>
    </div>
  );
}
