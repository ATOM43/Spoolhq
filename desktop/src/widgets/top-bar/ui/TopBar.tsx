import { Link } from "react-router";

import { useDaemonStatus } from "@/features/daemon-status";

import { StatusPill } from "./StatusPill";

export function TopBar() {
  const { status } = useDaemonStatus();
  return (
    <header className="flex h-12 shrink-0 items-center justify-between border-b bg-surface px-4">
      <Link to="/" className="text-sm font-semibold tracking-tight">
        SpoolHQ
      </Link>
      <StatusPill status={status} />
    </header>
  );
}
