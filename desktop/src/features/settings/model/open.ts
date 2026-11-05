import { useEffect } from "react";

export type SettingsTab = "agents" | "accounts" | "general" | "about";

type Listener = (tab: SettingsTab) => void;
const listeners = new Set<Listener>();

/** Open the Settings dialog of the current page (Home or the panel) on `tab`. */
export function openSettings(tab: SettingsTab = "agents") {
  for (const listener of listeners) {
    listener(tab);
  }
}

/** The dialog side of `openSettings`; `listener` must be stable. */
export function useOpenRequests(listener: Listener) {
  useEffect(() => {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  }, [listener]);
}
