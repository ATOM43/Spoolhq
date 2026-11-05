import { Outlet } from "react-router";

export function RootLayout() {
  return (
    <main className="h-full min-h-0 overflow-auto bg-surface">
      <Outlet />
    </main>
  );
}
