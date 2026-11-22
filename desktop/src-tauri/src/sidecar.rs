//! Starting the bundled daemon (docs/packaging.md).
//!
//! At launch the app asks the configured port for `GET /api/health` with the token. A
//! SpoolHQ answer means a daemon is already running and nothing is started; silence
//! means the bundled `spoolhq` binary is started with `serve` and given 15 s to answer;
//! any other answer means another program holds the port and nothing is started. A
//! daemon the app started is stopped when the app exits.

use std::future::Future;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::Duration;

use serde::Serialize;

use crate::daemon::{self, Http};

/// How long a started daemon gets to answer `/api/health`.
pub const START_TIMEOUT: Duration = Duration::from_secs(15);
const POLL_INTERVAL: Duration = Duration::from_millis(250);

/// What the app did about the daemon, shown on Home while the daemon doesn't answer.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(tag = "state", rename_all = "snake_case")]
pub enum LaunchState {
    /// The first health check is in flight.
    Checking,
    /// A SpoolHQ daemon was already running; the app uses it.
    External,
    /// The bundled daemon was started and is not answering yet.
    Starting,
    /// The bundled daemon was started and answered.
    Started,
    /// Another program answers on the port, so nothing was started.
    PortInUse { port: u16, config_path: String },
    /// The bundled daemon could not be started or did not answer in time.
    Failed { log_dir: String, message: String },
}

/// Who answers on the daemon's port.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Probe {
    SpoolHq,
    Nothing,
    Other,
}

/// A started daemon process, as the launch logic sees it.
pub trait Process {
    /// Whether the process has already exited.
    fn exited(&mut self) -> bool;
}

impl Process for Child {
    fn exited(&mut self) -> bool {
        !matches!(self.try_wait(), Ok(None))
    }
}

/// The end of a launch: the state to show, and the process if one was started.
pub struct Outcome<P> {
    pub state: LaunchState,
    pub process: Option<P>,
}

/// Check the port, start the daemon if nothing answers, and wait for it.
/// `on_starting` runs once the process is started, so Home can say so.
pub async fn launch<P, F, Fut>(
    probe: F,
    spawn: impl FnOnce() -> Result<P, String>,
    on_starting: impl FnOnce(),
    wait: Duration,
    paths: &LaunchPaths,
) -> Outcome<P>
where
    P: Process,
    F: Fn() -> Fut,
    Fut: Future<Output = Probe>,
{
    let failed = |message: String| LaunchState::Failed {
        log_dir: paths.log_dir.display().to_string(),
        message,
    };
    match probe().await {
        Probe::SpoolHq => return outcome(LaunchState::External, None),
        Probe::Other => {
            let state = LaunchState::PortInUse {
                port: paths.port,
                config_path: paths.config_path.display().to_string(),
            };
            return outcome(state, None);
        }
        Probe::Nothing => {}
    }
    let mut process = match spawn() {
        Ok(process) => process,
        Err(message) => return outcome(failed(message), None),
    };
    on_starting();
    let deadline = tokio::time::Instant::now() + wait;
    loop {
        if probe().await == Probe::SpoolHq {
            return outcome(LaunchState::Started, Some(process));
        }
        if process.exited() {
            return outcome(failed("the daemon exited during start".into()), None);
        }
        if tokio::time::Instant::now() >= deadline {
            let message = format!("no answer within {} s", wait.as_secs());
            // Kept: it is stopped with the app, and Home picks it up if it answers late.
            return outcome(failed(message), Some(process));
        }
        tokio::time::sleep(POLL_INTERVAL.min(wait)).await;
    }
}

fn outcome<P>(state: LaunchState, process: Option<P>) -> Outcome<P> {
    Outcome { state, process }
}

/// The paths and port a launch reports in its state.
pub struct LaunchPaths {
    pub port: u16,
    pub config_path: PathBuf,
    pub log_dir: PathBuf,
}

/// Whether a health reply comes from SpoolHQ: 200 with `{"status": "ok", "service": "spoolhq"}`.
pub fn is_spoolhq(status: u16, body: &str) -> bool {
    let Ok(value) = serde_json::from_str::<serde_json::Value>(body) else {
        return false;
    };
    status == 200 && value["status"] == "ok" && value["service"] == "spoolhq"
}

async fn probe_port(http: &Http, port: u16, token: Option<&str>) -> Probe {
    match http.health(port, token).await {
        Ok((status, body)) if is_spoolhq(status, &body) => Probe::SpoolHq,
        Ok(_) => Probe::Other,
        Err(_) => Probe::Nothing,
    }
}

/// The bundled binary: Tauri puts `externalBin` files next to the app's executable.
fn sidecar_path() -> Result<PathBuf, String> {
    let exe = std::env::current_exe().map_err(|err| err.to_string())?;
    let name = if cfg!(windows) {
        "spoolhq.exe"
    } else {
        "spoolhq"
    };
    Ok(exe.with_file_name(name))
}

fn spawn_sidecar(path: &Path) -> Result<Child, String> {
    let mut command = Command::new(path);
    command
        .arg("serve")
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        // CREATE_NO_WINDOW: no console window for the daemon.
        command.creation_flags(0x0800_0000);
    }
    command
        .spawn()
        .map_err(|err| format!("cannot start {}: {err}", path.display()))
}

/// The launch state and the daemon process the app started, if any.
pub struct Launcher {
    state: Mutex<LaunchState>,
    child: Mutex<Option<Child>>,
}

impl Default for Launcher {
    fn default() -> Self {
        Self {
            state: Mutex::new(LaunchState::Checking),
            child: Mutex::new(None),
        }
    }
}

impl Launcher {
    pub fn state(&self) -> LaunchState {
        self.state.lock().expect("launch state lock").clone()
    }

    fn set_state(&self, state: LaunchState) {
        *self.state.lock().expect("launch state lock") = state;
    }

    /// Find or start the daemon. Config errors leave the state for `daemon_info` to report.
    pub async fn start(&self, http: &Http) {
        let Ok(home) = daemon::current_home() else {
            return self.set_state(LaunchState::External);
        };
        let Ok(port) = daemon::read_port(&home, std::env::var_os(daemon::PORT_ENV_VAR)) else {
            return self.set_state(LaunchState::External);
        };
        let paths = LaunchPaths {
            port,
            config_path: home.join("config.toml"),
            log_dir: home.join("logs"),
        };
        let probe = || {
            let token = daemon::read_token(&home).ok().flatten();
            async move { probe_port(http, port, token.as_deref()).await }
        };
        let spawn = || sidecar_path().and_then(|path| spawn_sidecar(&path));
        let starting = || self.set_state(LaunchState::Starting);
        let result = launch(probe, spawn, starting, START_TIMEOUT, &paths).await;
        *self.child.lock().expect("daemon process lock") = result.process;
        self.set_state(result.state);
    }

    /// Stop the daemon this app started, if any (T49 keeps it running instead).
    pub fn stop(&self) {
        if let Some(mut child) = self.child.lock().expect("daemon process lock").take() {
            terminate(&mut child);
            let _ = child.wait();
        }
    }
}

/// Ask the daemon to stop, then kill it after 5 s. On Unix the one-file binary is a
/// launcher with the daemon as its child: SIGKILL would orphan the child, while SIGTERM
/// is passed on to it. On Windows it is a plain kill (unchecked there; T49 revisits).
fn terminate(child: &mut Child) {
    #[cfg(unix)]
    {
        let sent = Command::new("kill")
            .args(["-TERM", &child.id().to_string()])
            .status()
            .is_ok_and(|status| status.success());
        let deadline = std::time::Instant::now() + Duration::from_secs(5);
        while sent && std::time::Instant::now() < deadline {
            if child.exited() {
                return;
            }
            std::thread::sleep(Duration::from_millis(100));
        }
    }
    let _ = child.kill();
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::Cell;

    struct FakeProcess {
        exits: bool,
    }

    impl Process for FakeProcess {
        fn exited(&mut self) -> bool {
            self.exits
        }
    }

    fn paths() -> LaunchPaths {
        LaunchPaths {
            port: 8765,
            config_path: PathBuf::from("/h/config.toml"),
            log_dir: PathBuf::from("/h/logs"),
        }
    }

    /// Probes answer from `answers` in turn, then repeat the last one.
    fn run(
        answers: &[Probe],
        process: Result<FakeProcess, String>,
    ) -> (Outcome<FakeProcess>, usize, bool) {
        let calls = Cell::new(0);
        let spawned = Cell::new(false);
        let starting = Cell::new(false);
        let probe = || {
            let index = calls.get().min(answers.len() - 1);
            calls.set(calls.get() + 1);
            std::future::ready(answers[index])
        };
        let spawn = || {
            spawned.set(true);
            process
        };
        let runtime = tokio::runtime::Builder::new_current_thread()
            .enable_time()
            .build()
            .unwrap();
        let outcome = runtime.block_on(launch(
            probe,
            spawn,
            || starting.set(true),
            Duration::from_millis(600),
            &paths(),
        ));
        // Home says "Starting SpoolHQ…" only once a process is running.
        assert_eq!(
            starting.get(),
            outcome.process.is_some() || calls.get() == 2
        );
        (outcome, calls.get(), spawned.get())
    }

    #[test]
    fn a_running_spoolhq_is_used_and_nothing_is_started() {
        let (outcome, calls, spawned) = run(&[Probe::SpoolHq], Ok(FakeProcess { exits: false }));
        assert_eq!(outcome.state, LaunchState::External);
        assert!(outcome.process.is_none());
        assert_eq!(calls, 1);
        assert!(!spawned);
    }

    #[test]
    fn nothing_on_the_port_starts_the_sidecar_and_awaits_health() {
        let answers = [Probe::Nothing, Probe::Nothing, Probe::SpoolHq];
        let (outcome, calls, spawned) = run(&answers, Ok(FakeProcess { exits: false }));
        assert!(spawned);
        assert_eq!(outcome.state, LaunchState::Started);
        assert!(outcome.process.is_some());
        assert_eq!(calls, 3);
    }

    #[test]
    fn another_program_on_the_port_starts_nothing() {
        let (outcome, _, spawned) = run(&[Probe::Other], Ok(FakeProcess { exits: false }));
        assert!(!spawned);
        assert_eq!(
            outcome.state,
            LaunchState::PortInUse {
                port: 8765,
                config_path: "/h/config.toml".into()
            }
        );
    }

    #[test]
    fn no_health_in_time_is_the_failed_state_with_the_log_folder() {
        let (outcome, calls, spawned) = run(&[Probe::Nothing], Ok(FakeProcess { exits: false }));
        assert!(spawned);
        assert!(calls > 2, "health was polled until the deadline: {calls}");
        let LaunchState::Failed { log_dir, message } = outcome.state else {
            panic!("expected the failed state");
        };
        assert_eq!(log_dir, PathBuf::from("/h/logs").display().to_string());
        assert!(message.contains("no answer"), "{message}");
    }

    #[test]
    fn a_daemon_that_exits_or_cannot_start_fails_at_once() {
        let (outcome, calls, _) = run(&[Probe::Nothing], Ok(FakeProcess { exits: true }));
        assert!(matches!(outcome.state, LaunchState::Failed { .. }));
        assert!(outcome.process.is_none());
        assert_eq!(calls, 2);

        let (outcome, _, _) = run(&[Probe::Nothing], Err("cannot start x".into()));
        let LaunchState::Failed { message, .. } = outcome.state else {
            panic!("expected the failed state");
        };
        assert_eq!(message, "cannot start x");
    }

    #[cfg(unix)]
    #[test]
    fn terminate_stops_a_process_with_sigterm() {
        let mut child = Command::new("sleep").arg("30").spawn().unwrap();
        let started = std::time::Instant::now();
        terminate(&mut child);
        let status = child.wait().unwrap();
        assert!(started.elapsed() < Duration::from_secs(4));
        // Ended by the signal, not by the fallback kill.
        use std::os::unix::process::ExitStatusExt;
        assert_eq!(status.signal(), Some(15));
    }

    #[test]
    fn the_start_timeout_is_15_seconds() {
        assert_eq!(START_TIMEOUT, Duration::from_secs(15));
    }

    #[test]
    fn only_a_spoolhq_health_reply_counts() {
        assert!(is_spoolhq(200, r#"{"status":"ok","service":"spoolhq"}"#));
        assert!(!is_spoolhq(200, r#"{"status":"ok"}"#));
        assert!(!is_spoolhq(404, r#"{"status":"ok","service":"spoolhq"}"#));
        assert!(!is_spoolhq(200, "<html>"));
    }

    #[test]
    fn launch_states_serialise_with_a_state_tag() {
        let json = serde_json::to_value(LaunchState::PortInUse {
            port: 9000,
            config_path: "/h/config.toml".into(),
        })
        .unwrap();
        assert_eq!(
            json,
            serde_json::json!({ "state": "port_in_use", "port": 9000, "config_path": "/h/config.toml" })
        );
    }
}
