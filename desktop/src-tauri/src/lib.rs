//! SpoolHQ desktop app: a Tauri shell around the React UI.
//!
//! The webview talks to the daemon only through the commands in [`daemon`], which add
//! the bearer token on the Rust side, and [`events`], which holds the event WebSocket,
//! so the token never reaches JavaScript.

mod daemon;
mod events;

use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .manage(daemon::Http::default())
        .manage(events::Streams::default())
        .invoke_handler(tauri::generate_handler![
            daemon::daemon_info,
            daemon::daemon_get,
            daemon::daemon_request,
            events::events_subscribe,
            events::events_unsubscribe
        ])
        .on_window_event(|window, event| {
            if matches!(event, tauri::WindowEvent::Destroyed) {
                window.state::<events::Streams>().stop_all();
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running the SpoolHQ desktop app");
}
