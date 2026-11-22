//! The tray icon, closing the window, reopening and quitting: the Tauri side of
//! `quit.rs`. The tray, its menu and the quit dialog are native and need no capability;
//! the webview may only start the same quit (`app_quit`), for desktops without a tray.

use std::sync::atomic::{AtomicBool, Ordering};
use std::time::Duration;

use tauri::menu::{Menu, MenuItem, PredefinedMenuItem};
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
use tauri::{AppHandle, Manager, WebviewWindow, Wry};
use tauri_plugin_dialog::{DialogExt, MessageDialogButtons, MessageDialogKind};

use crate::daemon::{self, Http};
use crate::events::Streams;
use crate::quit::{self, CloseAction, QuitPlan};
use crate::sidecar::{LaunchState, Launcher};

/// How often the tray's status line is refreshed.
const STATUS_INTERVAL: Duration = Duration::from_secs(3);

/// Set while a quit is under way, so a second Quit or Cmd+Q doesn't start another.
#[derive(Default)]
pub struct Quitting(AtomicBool);

impl quit::Window for WebviewWindow {
    fn unminimize(&self) {
        let _ = WebviewWindow::unminimize(self);
    }
    fn show(&self) {
        let _ = WebviewWindow::show(self);
    }
    fn focus(&self) {
        let _ = self.set_focus();
    }
}

/// Show and focus the main window (Open, a left click, a second launch, the Dock).
pub fn show_main(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        quit::reopen(&window);
    }
}

/// The window's close button: hide while `desktop.keep_running` is on, else quit.
pub fn close_requested(window: &tauri::Window) {
    let keep_running = daemon::current_home().map_or(true, |home| quit::read_keep_running(&home));
    match quit::on_close(keep_running) {
        CloseAction::Hide => {
            let _ = window.hide();
        }
        CloseAction::Quit => request_quit(window.app_handle()),
    }
}

/// Build the tray icon and start refreshing its status line.
pub fn setup(app: &tauri::App) -> tauri::Result<()> {
    let status = MenuItem::with_id(app, "status", "Starting…", false, None::<&str>)?;
    let open = MenuItem::with_id(app, "open", "Open SpoolHQ", true, None::<&str>)?;
    let quit = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
    let separator = PredefinedMenuItem::separator(app)?;
    let menu = Menu::with_items(app, &[&status, &separator, &open, &quit])?;
    let mut tray = TrayIconBuilder::with_id("main")
        .tooltip("SpoolHQ")
        .menu(&menu)
        .show_menu_on_left_click(false)
        .on_menu_event(|app, event| match event.id().as_ref() {
            "open" => show_main(app),
            "quit" => request_quit(app),
            _ => {}
        })
        // Left clicks aren't reported on Linux; there the menu's Open does it.
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                show_main(tray.app_handle());
            }
        });
    if let Some(icon) = app.default_window_icon() {
        tray = tray.icon(icon.clone());
    }
    tray.build(app)?;

    let handle = app.handle().clone();
    tauri::async_runtime::spawn(async move {
        loop {
            refresh_status(&handle, &status).await;
            tokio::time::sleep(STATUS_INTERVAL).await;
        }
    });
    Ok(())
}

async fn refresh_status(app: &AppHandle, status: &MenuItem<Wry>) {
    let projects = fetch_projects(&app.state::<Http>()).await;
    let external = app.state::<Launcher>().state() == LaunchState::External;
    let _ = status.set_text(quit::status_line(projects.as_ref(), external));
}

async fn fetch_projects(http: &Http) -> Option<serde_json::Value> {
    let reply = daemon::send(http, "GET", "/api/projects", None, None, true)
        .await
        .ok()?;
    (reply.status == 200)
        .then(|| serde_json::from_str(&reply.body).ok())
        .flatten()
}

/// Settings → General's **Quit SpoolHQ**: the tray's Quit, where there is no tray.
#[tauri::command]
pub fn app_quit(app: AppHandle) {
    request_quit(&app);
}

/// Quit from the tray, the app menu, Cmd+Q, or closing with `keep_running` off.
pub fn request_quit(app: &AppHandle) {
    if app.state::<Quitting>().0.swap(true, Ordering::SeqCst) {
        return;
    }
    let app = app.clone();
    tauri::async_runtime::spawn(async move {
        let owns = app.state::<Launcher>().owns_daemon();
        let running = if owns {
            fetch_projects(&app.state::<Http>())
                .await
                .map(|projects| quit::running_tickets(&projects))
                .unwrap_or_default()
        } else {
            Vec::new()
        };
        match quit::plan(owns, &running) {
            QuitPlan::Confirm(text) => confirm(&app, text),
            QuitPlan::Shutdown => finish(app).await,
            QuitPlan::AppOnly => app.exit(0),
        }
    });
}

fn confirm(app: &AppHandle, text: String) {
    show_main(app);
    let answer = app.clone();
    app.dialog()
        .message(text)
        .title("Quit SpoolHQ?")
        .kind(MessageDialogKind::Warning)
        .buttons(MessageDialogButtons::OkCancelCustom(
            "Quit".into(),
            "Keep running".into(),
        ))
        .show(move |quit| {
            if quit {
                tauri::async_runtime::spawn(finish(answer));
            } else {
                answer.state::<Quitting>().0.store(false, Ordering::SeqCst);
            }
        });
}

/// Shut down the daemon the app started (`POST /api/shutdown`, then a kill after 15 s)
/// and exit.
async fn finish(app: AppHandle) {
    let http = app.state::<Http>();
    app.state::<Launcher>()
        .shut_down(|| async {
            daemon::send(&http, "POST", "/api/shutdown", None, None, true)
                .await
                .is_ok_and(|reply| reply.status == 200)
        })
        .await;
    app.state::<Streams>().stop_all();
    app.exit(0);
}
