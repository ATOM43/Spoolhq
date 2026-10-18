import { Settings } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";

/**
 * A Settings button and its (placeholder) dialog. It uses the native <dialog>, which
 * traps focus and closes on Escape without injecting inline styles (see the CSP).
 */
export function SettingsDialog() {
  const [open, setOpen] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const element = dialog.current;
    if (element === null) {
      return;
    }
    if (open && !element.open) {
      element.showModal();
    } else if (!open && element.open) {
      element.close();
    }
  }, [open]);

  return (
    <>
      <Button
        variant="outline"
        onClick={() => {
          setOpen(true);
        }}
      >
        <Settings aria-hidden />
        Settings
      </Button>
      <dialog
        ref={dialog}
        aria-labelledby="settings-title"
        onClose={() => {
          setOpen(false);
        }}
        className="m-auto w-full max-w-md rounded-lg border bg-surface p-6 text-ink shadow-lg backdrop:bg-black/50"
      >
        <h2 id="settings-title" className="text-lg font-semibold">
          Settings
        </h2>
        <p className="mt-2 text-sm text-ink-muted">
          Nothing to configure yet. Settings arrive in a later version.
        </p>
        <div className="mt-6 flex justify-end">
          <Button
            onClick={() => {
              setOpen(false);
            }}
          >
            Close
          </Button>
        </div>
      </dialog>
    </>
  );
}
