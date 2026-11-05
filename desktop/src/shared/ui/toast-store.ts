const SHOW_MS = 5000;
export interface Toast {
  text: string;
  tone: "success" | "error";
}
let current: Toast | null = null;
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) {
    listener();
  }
}

/** G2: a confirmation, top-right, for 5 s. One at a time; a newer one replaces it. */
export function showToast(text: string, tone: Toast["tone"] = "success") {
  const shown = { text, tone };
  current = shown;
  emit();
  setTimeout(() => {
    if (current === shown) {
      current = null;
      emit();
    }
  }, SHOW_MS);
}

export function subscribeToast(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export const currentToast = () => current;
