import { RotateCw } from "lucide-react";

import { Button } from "@/shared/ui";

/** "Couldn't load …" with **Retry**: the error state of every Run tab section. */
export function Failed({
  what,
  message,
  onRetry,
}: {
  what: string;
  message: string;
  onRetry: () => void;
}) {
  return (
    <div role="alert" className="flex flex-col items-start gap-2 p-6 text-sm">
      <p className="text-danger">
        Couldn't load {what}: {message}
      </p>
      <Button variant="outline" size="sm" onClick={onRetry}>
        <RotateCw aria-hidden />
        Retry
      </Button>
    </div>
  );
}
