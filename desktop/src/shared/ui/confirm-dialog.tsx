import type { ReactNode } from "react";

import { Button } from "./button";
import { Dialog } from "./dialog";

/** D4: one pattern for every irreversible step; the body states the consequence. */
export function ConfirmDialog({
  open,
  title,
  consequence,
  action,
  destructive = false,
  onConfirm,
  onCancel,
  children,
}: {
  open: boolean;
  title: string;
  consequence: string;
  /** The action as a verb: "Cancel run". */
  action: string;
  destructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  /** Optional details under the consequence, such as counts. */
  children?: ReactNode;
}) {
  return (
    <Dialog open={open} onClose={onCancel} title={title}>
      <p className="text-sm">{consequence}</p>
      {children}
      <div className="mt-6 flex justify-end gap-2">
        <Button variant="outline" onClick={onCancel}>
          Keep going
        </Button>
        <Button
          variant={destructive ? "destructive" : "default"}
          onClick={onConfirm}
        >
          {action}
        </Button>
      </div>
    </Dialog>
  );
}
