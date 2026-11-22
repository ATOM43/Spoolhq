//! SpoolHQ desktop app: a Tauri shell around the React UI.
//!
//! The webview talks to the daemon only through the commands in [`daemon`], which add
//! the bearer token on the Rust side, and [`events`], which holds the event WebSocket,
//! so the token never reaches JavaScript. Closing the window hides it and the tray
//! icon brings it back or quits ([`tray`], [`quit`]).

mod daemon;
mod events;
mod process;
mod quit;
mod sidecar;
mod tray;

use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // First, so a second launch exits before setting anything up.
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            tray::show_main(app);
        }))
        .plugin(tauri_plugin_dialog::init())
        .manage(daemon::Http::default())
        .manage(events::Streams::default())
        .manage(sidecar::Launcher::default())
        .manage(tray::Quitting::default())
        .setup(|app| {
            tray::setup(app)?;
            let handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                let http = handle.state::<daemon::Http>();
                handle.state::<sidecar::Launcher>().start(&http).await;
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            daemon::daemon_info,
            daemon::daemon_get,
            daemon::daemon_request,
            events::events_subscribe,
            events::events_unsubscribe,
            tray::app_quit
        ])
        .on_window_event(|window, event| match event {
            tauri::WindowEvent::CloseRequested { api, .. } => {
                api.prevent_close();
                tray::close_requested(window);
            }
            tauri::WindowEvent::Destroyed => window.state::<events::Streams>().stop_all(),
            _ => {}
        })
        .build(tauri::generate_context!())
        .expect("error while building the SpoolHQ desktop app")
        .run(|app, event| match event {
            // None: the user asked (Cmd+Q, the app menu); Some: `app.exit` after a quit.
            tauri::RunEvent::ExitRequested {
                code: None, api, ..
            } => {
                api.prevent_exit();
                tray::request_quit(app);
            }
            #[cfg(target_os = "macos")]
            tauri::RunEvent::Reopen { .. } => tray::show_main(app),
            // A last resort if the app exits without a clean quit.
            tauri::RunEvent::Exit => app.state::<sidecar::Launcher>().stop(),
            _ => {}
        });
}
