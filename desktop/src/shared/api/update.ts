/**
 * The update check, through the app's own Rust commands (`update_app.rs`): the webview
 * has no updater permission, and the feed is read and verified in Rust.
 */
import { invoke } from "@tauri-apps/api/core";

export type UpdateCheck =
  | { state: "unchecked" | "off" }
  | { state: "up_to_date" | "failed"; checked_at: number }
  | {
      state: "available";
      version: string;
      /** Plain text from the feed: render as text, never as HTML or links. */
      notes: string;
      /** Read, not enforced in v0.1.0. */
      minimum_version: string | null;
      checked_at: number;
    };

export interface UpdateStatus {
  current_version: string;
  check: UpdateCheck;
  /** `package`: a Linux `.deb` or `.rpm`, updated from the release page. */
  install: "in_place" | "package";
  external_daemon: boolean;
  installing: boolean;
  install_error: string | null;
}

/** The last check's result; `check: true` checks the feed first (**Check now**). */
export function getUpdateStatus(check = false): Promise<UpdateStatus> {
  return invoke<UpdateStatus>("update_status", { check });
}

/** **Install and restart**. On success the app restarts and this never resolves. */
export function installUpdate(): Promise<UpdateStatus> {
  return invoke<UpdateStatus>("update_install");
}
