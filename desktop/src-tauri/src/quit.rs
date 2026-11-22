//! Closing, reopening and quitting, as plain logic the Tauri glue in `tray.rs` calls
//! (docs/packaging.md).
//!
//! Closing the window hides it while `desktop.keep_running` is on (the default), so the
//! daemon and any run keep going. Quitting a daemon the app started asks it to shut
//! down (`POST /api/shutdown` cancels the run like Cancel does), confirming first when a
//! run is going; a daemon found running (`spool serve`) is left alone.

use std::future::Future;
use std::path::Path;
use std::time::Duration;

/// How long a daemon gets to end after `POST /api/shutdown` before it is killed.
pub const SHUTDOWN_TIMEOUT: Duration = Duration::from_secs(15);

/// What closing the window does.
#[derive(Debug, PartialEq, Eq)]
pub enum CloseAction {
    Hide,
    Quit,
}

pub fn on_close(keep_running: bool) -> CloseAction {
    if keep_running {
        CloseAction::Hide
    } else {
        CloseAction::Quit
    }
}

/// `[desktop] keep_running` in `config.toml`; on when missing or unreadable, so a broken
/// file never makes closing the window stop a run.
pub fn read_keep_running(home: &Path) -> bool {
    let Ok(text) = std::fs::read_to_string(home.join("config.toml")) else {
        return true;
    };
    let Ok(table) = text.parse::<toml::Table>() else {
        return true;
    };
    !matches!(
        table
            .get("desktop")
            .and_then(|desktop| desktop.get("keep_running")),
        Some(toml::Value::Boolean(false))
    )
}

/// The window, as reopening sees it.
pub trait Window {
    fn unminimize(&self);
    fn show(&self);
    fn focus(&self);
}

/// Show and focus the window: the tray's Open, a left click, or a second launch.
pub fn reopen(window: &impl Window) {
    window.unminimize();
    window.show();
    window.focus();
}

/// What Quit does once it knows who started the daemon and which runs are going.
#[derive(Debug, PartialEq, Eq)]
pub enum QuitPlan {
    /// A daemon the app started, with runs going: ask with this text first.
    Confirm(String),
    /// A daemon the app started, idle: shut it down without asking.
    Shutdown,
    /// A daemon the app didn't start: quit the app only.
    AppOnly,
}

pub fn plan(owns_daemon: bool, running: &[String]) -> QuitPlan {
    if !owns_daemon {
        return QuitPlan::AppOnly;
    }
    match running {
        [] => QuitPlan::Shutdown,
        [one] => QuitPlan::Confirm(format!(
            "A run is going ({one}). Quit stops it; the ticket goes back to Ready."
        )),
        many => QuitPlan::Confirm(format!(
            "Runs are going ({}). Quit stops them; the tickets go back to Ready.",
            many.join(", ")
        )),
    }
}

/// The tickets of active runs (running or paused) in a `GET /api/projects` answer.
pub fn running_tickets(projects: &serde_json::Value) -> Vec<String> {
    active(projects)
        .filter_map(|project| project["run"]["ticket_id"].as_str().map(str::to_owned))
        .collect()
}

fn active(projects: &serde_json::Value) -> impl Iterator<Item = &serde_json::Value> {
    projects
        .as_array()
        .into_iter()
        .flatten()
        .filter(|project| matches!(project["run_state"].as_str(), Some("running" | "paused")))
}

/// The tray's status line from a `GET /api/projects` answer (`None`: no answer).
/// `external`: the daemon was already running when the app started (`spool serve`).
pub fn status_line(projects: Option<&serde_json::Value>, external: bool) -> String {
    let Some(projects) = projects else {
        return "Daemon stopped".into();
    };
    let running = active(projects).find(|project| project["run_state"] == "running");
    let paused = active(projects).find(|project| project["run_state"] == "paused");
    let line = if let Some(project) = running {
        let ticket = project["run"]["ticket_id"].as_str().unwrap_or("a ticket");
        match project["run_step"].as_str().map(capitalise) {
            Some(step) => format!("Running {ticket} · {step}"),
            None => format!("Running {ticket}"),
        }
    } else if let Some(project) = paused {
        let reason = project["run"]["reason"].as_str().unwrap_or_default();
        if reason.contains("usage limit") {
            "Paused · usage limit".into()
        } else {
            "Paused".into()
        }
    } else {
        "Idle".into()
    };
    if external {
        format!("{line} · external daemon, keeps running after Quit")
    } else {
        line
    }
}

fn capitalise(word: &str) -> String {
    let mut chars = word.chars();
    chars.next().map_or_else(String::new, |first| {
        first.to_uppercase().chain(chars).collect()
    })
}

/// A daemon process, as shutting down sees it.
pub trait Stoppable {
    fn exited(&mut self) -> bool;
    fn terminate(&mut self);
    fn kill(&mut self);
}

impl Stoppable for crate::process::DaemonProcess {
    fn exited(&mut self) -> bool {
        Self::exited(self)
    }
    fn terminate(&mut self) {
        Self::terminate(self);
    }
    fn kill(&mut self) {
        Self::kill(self);
    }
}

/// Ask the daemon to shut down (`ask` resolves to whether it accepted), wait for the
/// process to end within `wait`, then kill whatever is left: the launcher if it hangs,
/// stray children in its group or job otherwise. Returns whether it ended by itself.
pub async fn shut_down<P: Stoppable>(
    process: &mut P,
    ask: impl Future<Output = bool>,
    wait: Duration,
) -> bool {
    let deadline = tokio::time::Instant::now() + wait;
    let accepted = tokio::time::timeout(wait, ask).await.unwrap_or(false);
    if !accepted {
        process.terminate();
    }
    while !process.exited() && tokio::time::Instant::now() < deadline {
        tokio::time::sleep(Duration::from_millis(100)).await;
    }
    let clean = process.exited();
    process.kill();
    clean
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use std::cell::RefCell;

    fn block_on<F: Future>(future: F) -> F::Output {
        tokio::runtime::Builder::new_current_thread()
            .enable_time()
            .build()
            .unwrap()
            .block_on(future)
    }

    #[test]
    fn closing_hides_with_keep_running_on_and_quits_with_it_off() {
        assert_eq!(on_close(true), CloseAction::Hide);
        assert_eq!(on_close(false), CloseAction::Quit);
    }

    #[test]
    fn keep_running_is_read_from_config_toml_and_defaults_on() {
        let home = tempfile::tempdir().unwrap();
        assert!(read_keep_running(home.path()));
        let config = home.path().join("config.toml");
        std::fs::write(&config, "port = 1\n[desktop]\nkeep_running = false\n").unwrap();
        assert!(!read_keep_running(home.path()));
        std::fs::write(&config, "[desktop]\nkeep_running = true\n").unwrap();
        assert!(read_keep_running(home.path()));
        std::fs::write(&config, "not toml [").unwrap();
        assert!(read_keep_running(home.path()));
    }

    #[derive(Default)]
    struct FakeWindow(RefCell<Vec<&'static str>>);

    impl Window for FakeWindow {
        fn unminimize(&self) {
            self.0.borrow_mut().push("unminimize");
        }
        fn show(&self) {
            self.0.borrow_mut().push("show");
        }
        fn focus(&self) {
            self.0.borrow_mut().push("focus");
        }
    }

    #[test]
    fn a_second_launch_shows_and_focuses_the_existing_window() {
        let window = FakeWindow::default();
        reopen(&window);
        assert_eq!(*window.0.borrow(), ["unminimize", "show", "focus"]);
    }

    #[test]
    fn quit_confirms_only_for_a_run_on_a_daemon_the_app_started() {
        assert_eq!(
            plan(true, &["T05".into()]),
            QuitPlan::Confirm(
                "A run is going (T05). Quit stops it; the ticket goes back to Ready.".into()
            )
        );
        assert_eq!(
            plan(true, &["T05".into(), "T02".into()]),
            QuitPlan::Confirm(
                "Runs are going (T05, T02). Quit stops them; the tickets go back to Ready.".into()
            )
        );
        assert_eq!(plan(true, &[]), QuitPlan::Shutdown);
        assert_eq!(plan(false, &["T05".into()]), QuitPlan::AppOnly);
    }

    fn projects() -> serde_json::Value {
        json!([
            { "name": "a", "run_state": "idle", "run": { "ticket_id": "T01" } },
            { "name": "b", "run_state": "paused",
              "run": { "ticket_id": "T03", "reason": "the implementer hit a usage limit" } },
            { "name": "c", "run_state": "running", "run": { "ticket_id": "T05" },
              "run_step": "implement" },
        ])
    }

    #[test]
    fn running_tickets_are_the_running_and_paused_runs() {
        assert_eq!(running_tickets(&projects()), ["T03", "T05"]);
        assert!(running_tickets(&json!({ "error": {} })).is_empty());
    }

    #[test]
    fn the_status_line_names_the_run_the_pause_or_idle() {
        assert_eq!(
            status_line(Some(&projects()), false),
            "Running T05 · Implement"
        );
        let paused = json!([projects()[1]]);
        assert_eq!(status_line(Some(&paused), false), "Paused · usage limit");
        let by_user = json!([{ "run_state": "paused", "run": { "reason": null } }]);
        assert_eq!(status_line(Some(&by_user), false), "Paused");
        assert_eq!(status_line(Some(&json!([])), false), "Idle");
        assert_eq!(status_line(None, true), "Daemon stopped");
        assert_eq!(
            status_line(Some(&json!([])), true),
            "Idle · external daemon, keeps running after Quit"
        );
    }

    /// Exits once `exits_after` checks have passed (never if `None`).
    struct FakeProcess {
        exits_after: Option<usize>,
        checks: usize,
        calls: Vec<&'static str>,
    }

    impl FakeProcess {
        fn new(exits_after: Option<usize>) -> Self {
            Self {
                exits_after,
                checks: 0,
                calls: Vec::new(),
            }
        }
    }

    impl Stoppable for FakeProcess {
        fn exited(&mut self) -> bool {
            self.checks += 1;
            self.exits_after.is_some_and(|after| self.checks > after)
        }
        fn terminate(&mut self) {
            self.calls.push("terminate");
        }
        fn kill(&mut self) {
            self.calls.push("kill");
        }
    }

    #[test]
    fn quit_asks_for_shutdown_and_waits_for_the_daemon_to_end() {
        let mut process = FakeProcess::new(Some(2));
        let clean = block_on(shut_down(
            &mut process,
            std::future::ready(true),
            Duration::from_secs(5),
        ));
        assert!(clean);
        // The final kill only sweeps up strays in the group or job.
        assert_eq!(process.calls, ["kill"]);
    }

    #[test]
    fn a_daemon_still_running_after_the_timeout_is_killed() {
        let mut process = FakeProcess::new(None);
        let started = std::time::Instant::now();
        let clean = block_on(shut_down(
            &mut process,
            std::future::ready(true),
            Duration::from_millis(300),
        ));
        assert!(!clean);
        assert!(started.elapsed() >= Duration::from_millis(300));
        assert_eq!(process.calls, ["kill"]);
    }

    #[test]
    fn a_refused_or_hanging_shutdown_request_falls_back_to_the_stop_signal() {
        let mut process = FakeProcess::new(Some(1));
        block_on(shut_down(
            &mut process,
            std::future::ready(false),
            Duration::from_secs(5),
        ));
        assert_eq!(process.calls, ["terminate", "kill"]);

        let mut process = FakeProcess::new(None);
        block_on(shut_down(
            &mut process,
            std::future::pending(),
            Duration::from_millis(200),
        ));
        assert_eq!(process.calls, ["terminate", "kill"]);
    }

    #[test]
    fn the_shutdown_timeout_is_15_seconds() {
        assert_eq!(SHUTDOWN_TIMEOUT, Duration::from_secs(15));
    }
}
