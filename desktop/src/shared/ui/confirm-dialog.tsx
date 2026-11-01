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
}: {
  open: boolean;
  title: string;
  consequence: string;
  /** The action as a verb: "Cancel run". */
  action: string;
  destructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <Dialog open={open} onClose={onCancel} title={title}>
      <p className="text-sm">{consequence}</p>
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
