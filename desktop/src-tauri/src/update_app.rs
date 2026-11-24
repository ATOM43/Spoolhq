//! The Tauri side of `update.rs`: the update feed is checked at launch, once the daemon is
//! up, and every 6 h, and the webview reads the result through `update_status` and starts
//! an install through `update_install`. The webview has no updater permission; the public
//! key comes only from `tauri.conf.json` (docs/packaging.md).

use std::sync::Mutex;
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use tauri::{AppHandle, Manager, Runtime};
use tauri_plugin_updater::{Update, UpdaterExt};

use crate::daemon::{self, Http};
use crate::events::Streams;
use crate::quit;
use crate::sidecar::{LaunchState, Launcher};
use crate::tray;
use crate::update::{self, Check, InstallSteps, Offer, UpdateStatus};

pub const CHECK_INTERVAL: Duration = Duration::from_secs(6 * 60 * 60);
const FEED_TIMEOUT: Duration = Duration::from_secs(30);

/// The last check, the update it found, and the state of an install.
pub struct Updates {
    check: Mutex<Check>,
    pending: Mutex<Option<Update>>,
    installing: AtomicBool,
    install_error: Mutex<Option<String>>,
    /// One check at a time: the timer and Check now share it.
    checking: tokio::sync::Mutex<()>,
}

impl Default for Updates {
    fn default() -> Self {
        Self {
            check: Mutex::new(Check::Unchecked),
            pending: Mutex::new(None),
            installing: AtomicBool::new(false),
            install_error: Mutex::new(None),
            checking: tokio::sync::Mutex::new(()),
        }
    }
}

fn now_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_or(0, |elapsed| {
            u64::try_from(elapsed.as_millis()).unwrap_or(u64::MAX)
        })
}

/// Ask the feed (unless `enabled` is false). The endpoint is the configured one, or in a
/// debug build `SPOOLHQ_DEV_UPDATE_FEED`; the public key is always the configured one.
async fn ask_feed<R: Runtime>(app: &AppHandle<R>, enabled: bool) -> (Check, Option<Update>) {
    let mut found = None;
    let slot = &mut found;
    let check = update::check(enabled, now_ms(), || async move {
        let mut builder = app.updater_builder().timeout(FEED_TIMEOUT);
        let dev = std::env::var(update::DEV_FEED_VAR).ok();
        if let Some(url) = update::dev_feed(dev.as_deref(), cfg!(debug_assertions)) {
            let url = url.parse::<tauri::Url>().map_err(|err| err.to_string())?;
            builder = builder
                .endpoints(vec![url])
                .map_err(|err| err.to_string())?;
        }
        let updater = builder.build().map_err(|err| err.to_string())?;
        let update = updater.check().await.map_err(|err| err.to_string())?;
        let offer = update.as_ref().map(|update| Offer {
            version: update.version.clone(),
            notes: update.body.clone().unwrap_or_default(),
            minimum_version: update::minimum_version(&update.raw_json),
        });
        *slot = update;
        Ok(offer)
    })
    .await;
    (check, found)
}

/// Check now, reading `desktop.check_updates` from `config.toml` (on when unreadable).
pub async fn run_check<R: Runtime>(app: &AppHandle<R>) {
    let updates = app.state::<Updates>();
    let _one = updates.checking.lock().await;
    let enabled =
        daemon::current_home().map_or(true, |home| quit::read_desktop_flag(&home, "check_updates"));
    let (check, found) = ask_feed(app, enabled).await;
    *updates.pending.lock().expect("update lock") = found;
    *updates.check.lock().expect("update lock") = check;
}

/// Check at launch (called once the daemon is up) and every [`CHECK_INTERVAL`].
pub fn spawn_checks(app: AppHandle) {
    tauri::async_runtime::spawn(async move {
        loop {
            run_check(&app).await;
            tokio::time::sleep(CHECK_INTERVAL).await;
        }
    });
}

fn status<R: Runtime>(app: &AppHandle<R>) -> UpdateStatus {
    let updates = app.state::<Updates>();
    UpdateStatus {
        current_version: app.package_info().version.to_string(),
        check: updates.check.lock().expect("update lock").clone(),
        install: update::install_kind(
            cfg!(target_os = "linux"),
            std::env::var_os("APPIMAGE").as_deref(),
        ),
        external_daemon: app.state::<Launcher>().state() == LaunchState::External,
        installing: updates.installing.load(Ordering::SeqCst),
        install_error: updates.install_error.lock().expect("update lock").clone(),
    }
}

/// The update state; `check: true` is About's **Check now**.
#[tauri::command]
pub async fn update_status(app: AppHandle, check: bool) -> UpdateStatus {
    if check {
        run_check(&app).await;
    }
    status(&app)
}

/// **Install and restart**: refused while a run is going; on success the app restarts and
/// this never answers.
#[tauri::command]
pub async fn update_install(app: AppHandle) -> UpdateStatus {
    let updates = app.state::<Updates>();
    if updates.installing.swap(true, Ordering::SeqCst) {
        return status(&app);
    }
    let pending = updates.pending.lock().expect("update lock").clone();
    let kind = status(&app).install;
    let result = match pending {
        Some(update) => update::install(&AppSteps { app: &app, update }, kind).await,
        None => Err("Check for updates first.".into()),
    };
    *updates.install_error.lock().expect("update lock") = result.err();
    updates.installing.store(false, Ordering::SeqCst);
    status(&app)
}

struct AppSteps<'a> {
    app: &'a AppHandle,
    update: Update,
}

impl InstallSteps for AppSteps<'_> {
    async fn download(&self) -> Result<Vec<u8>, String> {
        // `download` verifies the signature (and the signed version) before returning.
        self.update
            .download(|_, _| {}, || {})
            .await
            .map_err(|err| err.to_string())
    }
    async fn running(&self) -> Option<Vec<String>> {
        let projects = tray::fetch_projects(&self.app.state::<Http>()).await?;
        Some(quit::running_tickets(&projects))
    }
    fn owns_daemon(&self) -> bool {
        self.app.state::<Launcher>().owns_daemon()
    }
    async fn shut_down_daemon(&self) {
        let http = self.app.state::<Http>();
        self.app
            .state::<Launcher>()
            .shut_down(|| tray::ask_shutdown(&http))
            .await;
    }
    fn install(&self, bytes: &[u8]) -> Result<(), String> {
        self.update.install(bytes).map_err(|err| err.to_string())
    }
    async fn start_daemon(&self) {
        let http = self.app.state::<Http>();
        self.app.state::<Launcher>().start(&http).await;
    }
    fn restart_app(&self) {
        self.app.state::<Streams>().stop_all();
        self.app.restart();
    }
}

// The mock runtime isn't built on Windows (Cargo.toml).
#[cfg(all(test, not(windows)))]
mod tests {
    use super::*;
    use std::future::Future;
    use tauri::test::{MockRuntime, mock_builder, mock_context, noop_assets};
    use tokio::io::{AsyncReadExt, AsyncWriteExt};
    use tokio::net::TcpListener;

    const KEY_A: &str = include_str!("../fixtures/update/key-a.pub");
    const SIGNED_BY_A: &str = include_str!("../fixtures/update/signed-by-a.sig");
    const SIGNED_BY_B: &str = include_str!("../fixtures/update/signed-by-b.sig");
    const PACKAGE: &[u8] = include_bytes!("../fixtures/update/update.bin");

    fn block_on<F: Future>(future: F) -> F::Output {
        tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .unwrap()
            .block_on(future)
    }

    /// Serves `/latest.json` with `feed` and `/update.bin` with the fixture package.
    async fn serve(feed: String) -> String {
        let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
        let base = format!("http://{}", listener.local_addr().unwrap());
        tokio::spawn(async move {
            while let Ok((mut socket, _)) = listener.accept().await {
                let mut request = vec![0; 4096];
                let read = socket.read(&mut request).await.unwrap_or(0);
                let head = String::from_utf8_lossy(&request[..read]).into_owned();
                let body = if head.starts_with("GET /update.bin") {
                    PACKAGE.to_vec()
                } else {
                    feed.clone().into_bytes()
                };
                let reply = format!(
                    "HTTP/1.1 200 OK\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
                    body.len()
                );
                let _ = socket.write_all(reply.as_bytes()).await;
                let _ = socket.write_all(&body).await;
            }
        });
        base
    }

    fn feed(base: &str, version: &str, signature: &str) -> String {
        let entry =
            serde_json::json!({ "url": format!("{base}/update.bin"), "signature": signature });
        serde_json::json!({
            "version": version,
            "notes": "<b>Fixes</b>",
            "pub_date": "2026-11-24T10:00:00Z",
            "minimum_version": "0.1.0",
            "platforms": {
                "linux-x86_64": entry, "windows-x86_64": entry,
                "darwin-aarch64": entry, "darwin-x86_64": entry
            }
        })
        .to_string()
    }

    /// An app on version 0.1.0 that trusts key A and reads the feed at `endpoint`.
    fn app(endpoint: &str) -> tauri::App<MockRuntime> {
        let mut context = mock_context(noop_assets());
        context.config_mut().plugins.0.insert(
            "updater".into(),
            serde_json::json!({
                "pubkey": KEY_A.trim(), "requireSignedVersion": true, "endpoints": [endpoint]
            }),
        );
        mock_builder()
            .plugin(tauri_plugin_updater::Builder::new().build())
            .build(context)
            .unwrap()
    }

    async fn check_with(feed_body: Option<String>, enabled: bool) -> (Check, Option<Update>) {
        let endpoint = match feed_body {
            Some(body) => format!("{}/latest.json", serve(body).await),
            // A closed port: the request fails.
            None => "http://127.0.0.1:9/latest.json".into(),
        };
        let app = app(&endpoint);
        ask_feed(app.handle(), enabled).await
    }

    #[test]
    fn a_newer_version_is_available_with_its_notes_and_minimum_version() {
        block_on(async {
            let base = serve(String::new()).await;
            let body = feed(&base, "0.2.0", SIGNED_BY_A.trim());
            let (check, update) = check_with(Some(body), true).await;
            let Check::Available {
                version,
                notes,
                minimum_version,
                ..
            } = check
            else {
                panic!("{check:?}");
            };
            assert_eq!(
                (version.as_str(), notes.as_str()),
                ("0.2.0", "<b>Fixes</b>")
            );
            assert_eq!(minimum_version.as_deref(), Some("0.1.0"));
            assert!(update.is_some());
        });
    }

    #[test]
    fn the_same_version_is_up_to_date() {
        block_on(async {
            let body = feed("http://127.0.0.1:9", "0.1.0", SIGNED_BY_A.trim());
            let (check, update) = check_with(Some(body), true).await;
            assert!(matches!(check, Check::UpToDate { .. }), "{check:?}");
            assert!(update.is_none());
        });
    }

    #[test]
    fn a_malformed_feed_or_a_network_error_is_a_quiet_failure() {
        block_on(async {
            for body in [
                Some("<html>not json".to_owned()),
                Some("{}".to_owned()),
                None,
            ] {
                let (check, update) = check_with(body.clone(), true).await;
                assert!(matches!(check, Check::Failed { .. }), "{body:?}: {check:?}");
                assert!(update.is_none());
            }
        });
    }

    #[test]
    fn checks_off_ask_nothing() {
        block_on(async {
            let (check, update) = check_with(None, false).await;
            assert_eq!(check, Check::Off);
            assert!(update.is_none());
        });
    }

    /// The real download and verify, with the other steps recorded.
    struct Verifying {
        update: Update,
        installed: std::cell::Cell<bool>,
    }

    impl InstallSteps for Verifying {
        async fn download(&self) -> Result<Vec<u8>, String> {
            self.update
                .download(|_, _| {}, || {})
                .await
                .map_err(|err| err.to_string())
        }
        async fn running(&self) -> Option<Vec<String>> {
            Some(Vec::new())
        }
        fn owns_daemon(&self) -> bool {
            false
        }
        async fn shut_down_daemon(&self) {}
        fn install(&self, _bytes: &[u8]) -> Result<(), String> {
            self.installed.set(true);
            Ok(())
        }
        async fn start_daemon(&self) {}
        fn restart_app(&self) {}
    }

    async fn install_signed_by(signature: &str) -> (Result<(), String>, bool) {
        let base = serve(String::new()).await;
        let (_, update) = check_with(Some(feed(&base, "0.2.0", signature)), true).await;
        let steps = Verifying {
            update: update.expect("an update"),
            installed: false.into(),
        };
        let result = update::install(&steps, update::InstallKind::InPlace).await;
        (result, steps.installed.get())
    }

    #[test]
    fn an_update_signed_with_another_key_is_refused_and_nothing_installed() {
        block_on(async {
            assert_eq!(
                install_signed_by(SIGNED_BY_B.trim()).await,
                (Err(update::VERIFY_FAILED.into()), false)
            );
            // The same package signed with the trusted key goes through.
            assert_eq!(install_signed_by(SIGNED_BY_A.trim()).await, (Ok(()), true));
        });
    }

    #[test]
    fn checks_repeat_every_six_hours() {
        assert_eq!(CHECK_INTERVAL, Duration::from_secs(21_600));
    }
}
