import { Plus } from "lucide-react";
import { useState } from "react";

import { Button, Dialog } from "@/shared/ui";

import { CommandsStep } from "./CommandsStep";
import { CreateStep } from "./CreateStep";

/** The New project button and its two-step dialog: create, then test the commands. */
export function NewProjectButton({
  variant = "default",
}: {
  variant?: "default" | "outline";
}) {
  const [open, setOpen] = useState(false);
  const [created, setCreated] = useState<string | null>(null);
  const close = () => {
    setOpen(false);
    setCreated(null);
  };

  return (
    <>
      <Button
        variant={variant}
        onClick={() => {
          setOpen(true);
        }}
      >
        <Plus aria-hidden />
        New project
      </Button>
      <Dialog
        open={open}
        onClose={close}
        title={created === null ? "New project" : "Stack commands"}
        description={
          created === null
            ? "Link a git repository, or generate one from a template."
            : undefined
        }
      >
        {created === null ? (
          <CreateStep onCreated={setCreated} onCancel={close} />
        ) : (
          <CommandsStep name={created} onDone={close} />
        )}
      </Dialog>
    </>
  );
}
