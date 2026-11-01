import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useState } from "react";

import { saveSpec, type SpecFile } from "@/entities/project";
import { DaemonError, queryKeys } from "@/shared/api";

export const AUTOSAVE_MS = 1000;

export type SaveState = "saved" | "saving" | "unsaved" | "conflict" | "error";

/** The disk version a 412 sent back, or null if `error` isn't an edit conflict. */
function conflictOf(error: unknown): SpecFile | null {
  if (!(error instanceof DaemonError) || error.detail.kind !== "api") {
    return null;
  }
  const { status, etag, current } = error.detail;
  if (status !== 412 || etag === null) {
    return null;
  }
  const content =
    typeof current === "object" && current !== null && "content" in current
      ? String(current.content)
      : "";
  return { content, etag };
}

/**
 * The spec being edited, saved with `If-Match` 1 s after typing stops (or now with
 * `saveNow`). A 412 sets `conflict` and stops saving: only `reload` or `keepMine` (an
 * explicit click) moves on, so nothing is overwritten silently.
 */
export function useSpecAutosave(project: string, loaded: SpecFile) {
  const queryClient = useQueryClient();
  const [text, setText] = useState(loaded.content);
  const [saved, setSaved] = useState(loaded);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conflict, setConflict] = useState<SpecFile | null>(null);
  const dirty = text !== saved.content;

  const save = useCallback(
    async (etag: string) => {
      const content = text;
      setSaving(true);
      setError(null);
      try {
        const next = { content, etag: await saveSpec(project, content, etag) };
        setSaved(next);
        // So a remount starts from what is on disk now, not from the first load.
        queryClient.setQueryData(queryKeys.spec(project), next);
      } catch (failure) {
        const disk = conflictOf(failure);
        if (disk) {
          setConflict(disk);
        } else {
          setError(
            failure instanceof Error ? failure.message : String(failure),
          );
        }
      } finally {
        setSaving(false);
      }
    },
    [project, queryClient, text],
  );

  const idle = dirty && !saving && conflict === null && error === null;
  useEffect(() => {
    if (!idle) {
      return;
    }
    const timer = setTimeout(() => void save(saved.etag), AUTOSAVE_MS);
    return () => {
      clearTimeout(timer);
    };
  }, [idle, save, saved.etag]);

  const state: SaveState =
    conflict !== null
      ? "conflict"
      : saving
        ? "saving"
        : error !== null
          ? "error"
          : dirty
            ? "unsaved"
            : "saved";

  return {
    text,
    state,
    error,
    conflict,
    setText: (value: string) => {
      setText(value);
      setError(null); // a new edit tries again
    },
    saveNow: () => {
      if (dirty && !saving && conflict === null) {
        void save(saved.etag);
      }
    },
    /** Take the disk version and drop the local edits. */
    reload: () => {
      if (conflict !== null) {
        setText(conflict.content);
        setSaved(conflict);
        setConflict(null);
        queryClient.setQueryData(queryKeys.spec(project), conflict);
      }
    },
    /** Save the local text over the disk version the conflict reported. */
    keepMine: () => {
      if (conflict !== null) {
        setConflict(null);
        void save(conflict.etag);
      }
    },
  };
}
