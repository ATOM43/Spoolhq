//! SpoolHQ desktop app: a Tauri shell around the React UI.
//!
//! The webview talks to the daemon only through the commands in [`daemon`], which add
//! the bearer token on the Rust side, so the token never reaches JavaScript.

mod daemon;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(daemon::Http::default())
        .invoke_handler(tauri::generate_handler![
            daemon::daemon_info,
            daemon::daemon_get
        ])
        .run(tauri::generate_context!())
        .expect("error while running the SpoolHQ desktop app");
}
