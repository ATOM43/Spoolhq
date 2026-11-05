import { CircleCheck } from "lucide-react";
import { useSyncExternalStore } from "react";

import { currentToast, subscribeToast } from "./toast-store";

/** Where `showToast` shows; mounted once by the app. */
export function Toaster() {
  const text = useSyncExternalStore(subscribeToast, currentToast);
  return (
    <div aria-live="polite" className="fixed top-4 right-4 z-50">
      {text ? (
        <p className="flex items-center gap-2 rounded-lg border bg-surface px-4 py-3 text-sm shadow-lg">
          <CircleCheck aria-hidden className="size-4 text-success" />
          {text}
        </p>
      ) : null}
    </div>
  );
}
