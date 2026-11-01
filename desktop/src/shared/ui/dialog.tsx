import { useEffect, useRef, type ReactNode } from "react";

/**
 * A modal dialog on the native <dialog>, which traps focus and closes on Escape
 * without injecting inline styles (see the CSP).
 */
export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string | undefined;
  children: ReactNode;
}) {
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
    <dialog
      ref={dialog}
      aria-label={title}
      onClose={onClose}
      className="m-auto w-full max-w-xl rounded-lg border bg-surface p-6 text-ink shadow-lg backdrop:bg-black/50"
    >
      {open ? (
        <>
          <h2 className="text-lg font-semibold">{title}</h2>
          {description ? (
            <p className="mt-1 text-sm text-ink-muted">{description}</p>
          ) : null}
          <div className="mt-6">{children}</div>
        </>
      ) : null}
    </dialog>
  );
}
