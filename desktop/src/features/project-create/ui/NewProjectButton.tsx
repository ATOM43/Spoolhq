import { useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useCallback, useState } from "react";
import { useNavigate } from "react-router";

import { queryKeys } from "@/shared/api";
import { Button, Dialog, showToast } from "@/shared/ui";

import { NewProjectForm } from "./NewProjectForm";

export const CREATED_TOAST = "Project created — write your spec next";

/** The New project button and D1, its dialog. */
export function NewProjectButton({
  variant = "default",
}: {
  variant?: "default" | "outline";
}) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const close = useCallback(() => {
    setOpen(false);
    setBusy(false);
  }, []);
  const created = useCallback(
    (name: string) => {
      close();
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      void navigate(`/p/${name}?tab=spec`);
      showToast(CREATED_TOAST);
    },
    [close, navigate, queryClient],
  );

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
        closable={!busy}
        title="New project"
        className="max-h-[calc(100vh-2rem)] max-w-[560px] overflow-y-auto"
      >
        <NewProjectForm onClose={close} onBusy={setBusy} onCreated={created} />
      </Dialog>
    </>
  );
}
