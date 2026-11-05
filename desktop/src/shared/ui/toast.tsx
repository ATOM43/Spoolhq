import { CircleCheck, CircleX } from "lucide-react";
import { useSyncExternalStore } from "react";

import { currentToast, subscribeToast } from "./toast-store";

/** Where `showToast` shows; mounted once by the app. */
export function Toaster() {
  const toast = useSyncExternalStore(subscribeToast, currentToast);
  return (
    <div aria-live="polite" className="fixed top-4 right-4 z-50">
      {toast ? (
        <p className="flex items-center gap-2 rounded-lg border bg-surface px-4 py-3 text-sm shadow-lg">
          {toast.tone === "error" ? (
            <CircleX aria-hidden className="size-4 text-danger" />
          ) : (
            <CircleCheck aria-hidden className="size-4 text-success" />
          )}
          {toast.text}
        </p>
      ) : null}
    </div>
  );
}
