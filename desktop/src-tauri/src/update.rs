//! The update check and Install and restart, as plain logic the Tauri glue in
//! `update_app.rs` calls (docs/packaging.md).
//!
//! The feed is read from Rust only; the webview sees an [`UpdateStatus`] and can ask for a
//! check or an install, nothing more. An install never happens while a run is going, and a
//! daemon the app started is shut down cleanly between verifying the download and
//! installing it.

use std::future::Future;

use serde::Serialize;

/// The variable that points a debug build at a local feed.
pub const DEV_FEED_VAR: &str = "SPOOLHQ_DEV_UPDATE_FEED";
pub const VERIFY_FAILED: &str = "The update couldn't be verified; nothing was installed.";
pub const PACKAGE_INSTALL: &str = "Download the new package from the release page";
pub const NO_DAEMON: &str = "Couldn't ask the daemon whether a run is going; try again.";
pub const INSTALL_FAILED: &str = "The update couldn't be installed; SpoolHQ wasn't changed.";

/// The last check's outcome. Times are Unix milliseconds; the webview formats them.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(tag = "state", rename_all = "snake_case")]
pub enum Check {
    /// No check has finished yet.
    Unchecked,
    /// `desktop.check_updates` is off; no request was made.
    Off,
    UpToDate {
        checked_at: u64,
    },
    Available {
        version: String,
        /// Plain text: the webview shows it as text, never as HTML or links.
        notes: String,
        /// Read from the feed, not enforced in v0.1.0.
        minimum_version: Option<String>,
        checked_at: u64,
    },
    /// The request, the feed or its parsing failed; About shows one quiet line.
    Failed {
        checked_at: u64,
    },
}

/// How this copy of the app gets updates.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum InstallKind {
    /// The updater replaces the app: Windows, macOS, the Linux AppImage.
    InPlace,
    /// A Linux `.deb` or `.rpm`: the package manager owns the files.
    Package,
}

/// The AppImage runtime sets `APPIMAGE` for the app it starts; a `.deb` or `.rpm` install
/// is started without it.
pub fn install_kind(linux: bool, appimage: Option<&std::ffi::OsStr>) -> InstallKind {
    if linux && appimage.is_none_or(std::ffi::OsStr::is_empty) {
        InstallKind::Package
    } else {
        InstallKind::InPlace
    }
}

/// What the webview gets from `update_status`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct UpdateStatus {
    pub current_version: String,
    pub check: Check,
    pub install: InstallKind,
    /// The daemon was running before the app (`spool serve`); an update leaves it running.
    pub external_daemon: bool,
    pub installing: bool,
    /// Why the last Install and restart stopped, in fixed words.
    pub install_error: Option<String>,
}

/// The feed a debug build may use instead of the configured one: only `http://127.0.0.1`.
/// Release builds (`debug == false`) ignore the variable.
pub fn dev_feed(value: Option<&str>, debug: bool) -> Option<String> {
    let value = value?.trim();
    let rest = value.strip_prefix("http://127.0.0.1")?;
    let local = rest.is_empty() || rest.starts_with(':') || rest.starts_with('/');
    (debug && local).then(|| value.to_owned())
}

/// The feed's answer, reduced to what the status needs. `None`: not newer than this app.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Offer {
    pub version: String,
    pub notes: String,
    pub minimum_version: Option<String>,
}

/// `minimum_version` from the feed's JSON; empty or missing means none.
pub fn minimum_version(feed: &serde_json::Value) -> Option<String> {
    feed["minimum_version"]
        .as_str()
        .map(str::trim)
        .filter(|version| !version.is_empty())
        .map(str::to_owned)
}

/// Run one check unless checks are off. `fetch` asks the feed: `Ok(None)` is up to date,
/// `Err` any failure (network, status, malformed feed, no entry for this platform).
pub async fn check<F, Fut>(enabled: bool, now: u64, fetch: F) -> Check
where
    F: FnOnce() -> Fut,
    Fut: Future<Output = Result<Option<Offer>, String>>,
{
    if !enabled {
        return Check::Off;
    }
    match fetch().await {
        Ok(None) => Check::UpToDate { checked_at: now },
        Ok(Some(offer)) => Check::Available {
            version: offer.version,
            notes: offer.notes,
            minimum_version: offer.minimum_version,
            checked_at: now,
        },
        Err(_) => Check::Failed { checked_at: now },
    }
}

/// "Wait for the run to finish (T05)", the Install button's reason.
pub fn wait_reason(running: &[String]) -> String {
    match running {
        [one] => format!("Wait for the run to finish ({one})"),
        many => format!("Wait for the runs to finish ({})", many.join(", ")),
    }
}

/// The steps of Install and restart, so their order can be tested without an app.
pub trait InstallSteps {
    /// Download the update and verify its signature; the bytes only if it verified.
    fn download(&self) -> impl Future<Output = Result<Vec<u8>, String>>;
    /// The tickets of runs going in any project (`None`: the daemon didn't answer).
    fn running(&self) -> impl Future<Output = Option<Vec<String>>>;
    fn owns_daemon(&self) -> bool;
    /// `POST /api/shutdown` and wait for the daemon the app started to end.
    fn shut_down_daemon(&self) -> impl Future<Output = ()>;
    fn install(&self, bytes: &[u8]) -> Result<(), String>;
    /// Start the daemon again after a failed install.
    fn start_daemon(&self) -> impl Future<Output = ()>;
    fn restart_app(&self);
}

/// Download and verify, check with the daemon that no run is going, shut down a daemon
/// the app started, install, restart. Any refusal or failure returns its message and
/// installs nothing.
pub async fn install(steps: &impl InstallSteps, kind: InstallKind) -> Result<(), String> {
    if kind == InstallKind::Package {
        return Err(PACKAGE_INSTALL.into());
    }
    let bytes = steps
        .download()
        .await
        .map_err(|_| VERIFY_FAILED.to_owned())?;
    match steps.running().await {
        None => return Err(NO_DAEMON.into()),
        Some(running) if !running.is_empty() => return Err(wait_reason(&running)),
        Some(_) => {}
    }
    let owned = steps.owns_daemon();
    if owned {
        steps.shut_down_daemon().await;
    }
    if steps.install(&bytes).is_err() {
        if owned {
            steps.start_daemon().await;
        }
        return Err(INSTALL_FAILED.into());
    }
    steps.restart_app();
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::{Cell, RefCell};
    use std::ffi::OsStr;

    fn block_on<F: Future>(future: F) -> F::Output {
        tokio::runtime::Builder::new_current_thread()
            .build()
            .unwrap()
            .block_on(future)
    }

    fn offer() -> Offer {
        Offer {
            version: "0.2.0".into(),
            notes: "Fixes".into(),
            minimum_version: None,
        }
    }

    #[test]
    fn a_newer_version_is_available_and_none_is_up_to_date() {
        let available = block_on(check(true, 7, || async { Ok(Some(offer())) }));
        assert_eq!(
            available,
            Check::Available {
                version: "0.2.0".into(),
                notes: "Fixes".into(),
                minimum_version: None,
                checked_at: 7
            }
        );
        let same = block_on(check(true, 8, || async { Ok(None) }));
        assert_eq!(same, Check::UpToDate { checked_at: 8 });
        let failed = block_on(check(true, 9, || async { Err("timeout".into()) }));
        assert_eq!(failed, Check::Failed { checked_at: 9 });
    }

    #[test]
    fn checks_off_make_no_request() {
        let asked = Cell::new(false);
        let result = block_on(check(false, 1, || {
            asked.set(true);
            async { Ok(None) }
        }));
        assert_eq!(result, Check::Off);
        assert!(!asked.get());
    }

    #[test]
    fn minimum_version_is_read_from_the_feed() {
        let feed = serde_json::json!({ "version": "0.2.0", "minimum_version": "0.1.5" });
        assert_eq!(minimum_version(&feed).as_deref(), Some("0.1.5"));
        assert_eq!(
            minimum_version(&serde_json::json!({ "minimum_version": " " })),
            None
        );
        assert_eq!(minimum_version(&serde_json::json!({})), None);
    }

    #[test]
    fn the_dev_feed_is_local_http_in_debug_builds_only() {
        let local = "http://127.0.0.1:9000/latest.json";
        assert_eq!(dev_feed(Some(local), true).as_deref(), Some(local));
        assert_eq!(dev_feed(Some(local), false), None);
        assert_eq!(dev_feed(None, true), None);
        for other in [
            "https://127.0.0.1:9000/latest.json",
            "http://127.0.0.1.evil.example/latest.json",
            "http://localhost:9000/latest.json",
            "http://example.com/latest.json",
        ] {
            assert_eq!(dev_feed(Some(other), true), None, "{other}");
        }
    }

    #[test]
    fn deb_and_rpm_installs_are_told_apart_by_how_the_app_started() {
        let path = OsStr::new("/home/me/SpoolHQ.AppImage");
        assert_eq!(install_kind(true, Some(path)), InstallKind::InPlace);
        assert_eq!(install_kind(true, None), InstallKind::Package);
        assert_eq!(
            install_kind(true, Some(OsStr::new(""))),
            InstallKind::Package
        );
        assert_eq!(install_kind(false, None), InstallKind::InPlace);
    }

    #[test]
    fn the_status_serializes_for_the_webview() {
        let status = UpdateStatus {
            current_version: "0.1.0".into(),
            check: Check::Failed { checked_at: 5 },
            install: InstallKind::Package,
            external_daemon: false,
            installing: false,
            install_error: None,
        };
        let json = serde_json::to_value(status).unwrap();
        assert_eq!(
            json["check"],
            serde_json::json!({ "state": "failed", "checked_at": 5 })
        );
        assert_eq!(json["install"], "package");
    }

    struct Fake {
        download: Result<Vec<u8>, String>,
        running: Option<Vec<String>>,
        owns: bool,
        install_ok: bool,
        calls: RefCell<Vec<&'static str>>,
    }

    impl Fake {
        fn new() -> Self {
            Self {
                download: Ok(b"app".to_vec()),
                running: Some(Vec::new()),
                owns: true,
                install_ok: true,
                calls: RefCell::default(),
            }
        }
        fn calls(&self) -> Vec<&'static str> {
            self.calls.borrow().clone()
        }
    }

    impl InstallSteps for Fake {
        async fn download(&self) -> Result<Vec<u8>, String> {
            self.calls.borrow_mut().push("download");
            self.download.clone()
        }
        async fn running(&self) -> Option<Vec<String>> {
            self.calls.borrow_mut().push("running");
            self.running.clone()
        }
        fn owns_daemon(&self) -> bool {
            self.owns
        }
        async fn shut_down_daemon(&self) {
            self.calls.borrow_mut().push("shutdown");
        }
        fn install(&self, bytes: &[u8]) -> Result<(), String> {
            assert_eq!(bytes, b"app");
            self.calls.borrow_mut().push("install");
            if self.install_ok {
                Ok(())
            } else {
                Err("disk full".into())
            }
        }
        async fn start_daemon(&self) {
            self.calls.borrow_mut().push("start");
        }
        fn restart_app(&self) {
            self.calls.borrow_mut().push("restart");
        }
    }

    #[test]
    fn an_app_started_daemon_is_shut_down_after_verifying_and_before_installing() {
        let fake = Fake::new();
        assert_eq!(block_on(install(&fake, InstallKind::InPlace)), Ok(()));
        assert_eq!(
            fake.calls(),
            ["download", "running", "shutdown", "install", "restart"]
        );
    }

    #[test]
    fn an_external_daemon_keeps_running() {
        let fake = Fake {
            owns: false,
            ..Fake::new()
        };
        assert_eq!(block_on(install(&fake, InstallKind::InPlace)), Ok(()));
        assert_eq!(fake.calls(), ["download", "running", "install", "restart"]);
    }

    #[test]
    fn install_is_refused_while_a_run_is_going() {
        let fake = Fake {
            running: Some(vec!["T05".into()]),
            ..Fake::new()
        };
        assert_eq!(
            block_on(install(&fake, InstallKind::InPlace)),
            Err("Wait for the run to finish (T05)".into())
        );
        assert_eq!(fake.calls(), ["download", "running"]);
        assert_eq!(
            wait_reason(&["T05".into(), "T02".into()]),
            "Wait for the runs to finish (T05, T02)"
        );
        let silent = Fake {
            running: None,
            ..Fake::new()
        };
        assert_eq!(
            block_on(install(&silent, InstallKind::InPlace)),
            Err(NO_DAEMON.into())
        );
        assert!(!silent.calls().contains(&"install"));
    }

    #[test]
    fn a_failed_download_or_signature_installs_nothing() {
        let fake = Fake {
            download: Err("signature".into()),
            ..Fake::new()
        };
        assert_eq!(
            block_on(install(&fake, InstallKind::InPlace)),
            Err(VERIFY_FAILED.into())
        );
        assert_eq!(fake.calls(), ["download"]);
    }

    #[test]
    fn a_failed_install_starts_the_daemon_again() {
        let fake = Fake {
            install_ok: false,
            ..Fake::new()
        };
        assert_eq!(
            block_on(install(&fake, InstallKind::InPlace)),
            Err(INSTALL_FAILED.into())
        );
        assert_eq!(
            fake.calls(),
            ["download", "running", "shutdown", "install", "start"]
        );
    }

    #[test]
    fn package_installs_never_install() {
        let fake = Fake::new();
        assert_eq!(
            block_on(install(&fake, InstallKind::Package)),
            Err(PACKAGE_INSTALL.into())
        );
        assert!(fake.calls().is_empty());
    }
}
