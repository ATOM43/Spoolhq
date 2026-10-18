//! Finding and calling the local SpoolHQ daemon.
//!
//! The port and token are read the way the daemon and the `spool` CLI read them: the
//! home folder is `SPOOLHQ_HOME` or `~/.spoolhq`, the port comes from `SPOOLHQ_PORT`,
//! then `config.toml`, then 8765, and the token is the `token` file in the home folder.
//! Both are re-read on every call, so starting the daemon after the app just works.

use std::ffi::OsString;
use std::path::{Path, PathBuf};
use std::time::Duration;

use serde::Serialize;

pub const HOME_ENV_VAR: &str = "SPOOLHQ_HOME";
pub const PORT_ENV_VAR: &str = "SPOOLHQ_PORT";
pub const DEFAULT_PORT: u16 = 8765;
/// The daemon only ever listens here (DECISIONS.md, entry 17).
const DAEMON_HOST: &str = "127.0.0.1";

/// What the webview may know about the daemon: never the token itself.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct DaemonInfo {
    pub port: u16,
    pub token_present: bool,
    pub token_path: String,
}

/// The daemon's answer, passed through for the TypeScript client to interpret.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct DaemonReply {
    pub status: u16,
    pub body: String,
}

/// Failures before an HTTP status exists. Serialised as `{ "kind": ..., ... }`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum DaemonError {
    /// Nothing answered on the daemon's port.
    NotRunning { port: u16, message: String },
    /// The request needs the token and the token file is missing or empty.
    TokenMissing { path: String },
    /// `config.toml` or `SPOOLHQ_PORT` is unreadable or invalid.
    Config { message: String },
    /// The webview asked for something this command does not allow.
    InvalidRequest { message: String },
}

/// The home folder: `SPOOLHQ_HOME` if set and non-empty, else `~/.spoolhq`.
pub fn home_dir(env_home: Option<OsString>) -> Result<PathBuf, DaemonError> {
    match env_home {
        Some(home) if !home.is_empty() => Ok(PathBuf::from(home)),
        _ => dirs::home_dir()
            .map(|home| home.join(".spoolhq"))
            .ok_or_else(|| DaemonError::Config {
                message: format!("cannot find your home folder; set {HOME_ENV_VAR}"),
            }),
    }
}

pub fn token_path(home: &Path) -> PathBuf {
    home.join("token")
}

/// The saved token, or `None` if the file is missing or empty.
pub fn read_token(home: &Path) -> Result<Option<String>, DaemonError> {
    let path = token_path(home);
    match std::fs::read_to_string(&path) {
        Ok(text) => {
            let token = text.trim();
            Ok((!token.is_empty()).then(|| token.to_owned()))
        }
        Err(err) if err.kind() == std::io::ErrorKind::NotFound => Ok(None),
        Err(err) => Err(DaemonError::Config {
            message: format!("cannot read {}: {err}", path.display()),
        }),
    }
}

/// The daemon's port: `SPOOLHQ_PORT`, then `port` in `config.toml`, then 8765.
pub fn read_port(home: &Path, env_port: Option<OsString>) -> Result<u16, DaemonError> {
    if let Some(value) = env_port {
        let text = value.to_string_lossy();
        return parse_port(text.trim())
            .ok_or_else(|| invalid_port(&format!("environment variable {PORT_ENV_VAR}")));
    }

    let path = home.join("config.toml");
    let text = match std::fs::read_to_string(&path) {
        Ok(text) => text,
        Err(err) if err.kind() == std::io::ErrorKind::NotFound => return Ok(DEFAULT_PORT),
        Err(err) => {
            return Err(DaemonError::Config {
                message: format!("cannot read {}: {err}", path.display()),
            });
        }
    };
    let table: toml::Table = text.parse().map_err(|err| DaemonError::Config {
        message: format!("invalid config file {}: {err}", path.display()),
    })?;
    let source = path.display().to_string();
    match table.get("port") {
        None => Ok(DEFAULT_PORT),
        Some(toml::Value::Integer(port)) => u16::try_from(*port)
            .ok()
            .filter(|port| *port != 0)
            .ok_or_else(|| invalid_port(&source)),
        // The daemon (pydantic) also accepts a quoted number.
        Some(toml::Value::String(port)) => parse_port(port).ok_or_else(|| invalid_port(&source)),
        Some(_) => Err(invalid_port(&source)),
    }
}

fn parse_port(text: &str) -> Option<u16> {
    text.parse::<u16>().ok().filter(|port| *port != 0)
}

fn invalid_port(source: &str) -> DaemonError {
    DaemonError::Config {
        message: format!("invalid setting 'port' ({source}): must be a number from 1 to 65535"),
    }
}

pub fn info(home: &Path, env_port: Option<OsString>) -> Result<DaemonInfo, DaemonError> {
    Ok(DaemonInfo {
        port: read_port(home, env_port)?,
        token_present: read_token(home)?.is_some(),
        token_path: token_path(home).display().to_string(),
    })
}

/// Build the request URL. Only `/api/...` paths on 127.0.0.1 can be requested, so the
/// webview cannot use this command to reach any other host or scheme.
pub fn api_url(port: u16, path: &str) -> Result<String, DaemonError> {
    let allowed = path.starts_with("/api/")
        && !path.split('/').any(|segment| segment == "..")
        && path
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || b"/-_.".contains(&byte));
    if !allowed {
        return Err(DaemonError::InvalidRequest {
            message: format!("not a daemon API path: {path:?}"),
        });
    }
    Ok(format!("http://{DAEMON_HOST}:{port}{path}"))
}

/// The HTTP client shared by all commands.
pub struct Http(reqwest::Client);

impl Default for Http {
    fn default() -> Self {
        let client = reqwest::Client::builder()
            // The daemon is local, so HTTP(S)_PROXY must not apply (DECISIONS.md, 23).
            .no_proxy()
            .connect_timeout(Duration::from_secs(2))
            .timeout(Duration::from_secs(5))
            .build()
            .expect("the HTTP client has a static, valid configuration");
        Self(client)
    }
}

fn current_home() -> Result<PathBuf, DaemonError> {
    home_dir(std::env::var_os(HOME_ENV_VAR))
}

/// The daemon's port and whether a token exists. Never returns the token.
#[tauri::command]
pub fn daemon_info() -> Result<DaemonInfo, DaemonError> {
    info(&current_home()?, std::env::var_os(PORT_ENV_VAR))
}

/// `GET http://127.0.0.1:<port><path>`, adding the token when `authenticated` is set.
#[tauri::command]
pub async fn daemon_get(
    http: tauri::State<'_, Http>,
    path: String,
    authenticated: bool,
) -> Result<DaemonReply, DaemonError> {
    let home = current_home()?;
    let port = read_port(&home, std::env::var_os(PORT_ENV_VAR))?;
    let url = api_url(port, &path)?;

    let mut request = http.0.get(url);
    if authenticated {
        let token = read_token(&home)?.ok_or_else(|| DaemonError::TokenMissing {
            path: token_path(&home).display().to_string(),
        })?;
        request = request.bearer_auth(token);
    }

    let not_running = |err: reqwest::Error| DaemonError::NotRunning {
        port,
        // Without the URL: it is fixed, and error text should stay short.
        message: err.without_url().to_string(),
    };
    let response = request.send().await.map_err(not_running)?;
    let status = response.status().as_u16();
    let body = response.text().await.map_err(not_running)?;
    Ok(DaemonReply { status, body })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn temp_home() -> tempfile::TempDir {
        tempfile::tempdir().expect("create temp dir")
    }

    #[test]
    fn spoolhq_home_overrides_the_default_folder() {
        let home = temp_home();
        let resolved = home_dir(Some(home.path().as_os_str().to_owned())).unwrap();
        assert_eq!(resolved, home.path());
    }

    #[test]
    fn empty_spoolhq_home_falls_back_to_the_default_folder() {
        let resolved = home_dir(Some(OsString::new())).unwrap();
        assert!(resolved.ends_with(".spoolhq"));
    }

    #[test]
    fn port_defaults_to_8765_without_a_config_file() {
        let home = temp_home();
        assert_eq!(read_port(home.path(), None).unwrap(), DEFAULT_PORT);
    }

    #[test]
    fn port_is_read_from_config_toml() {
        let home = temp_home();
        std::fs::write(
            home.path().join("config.toml"),
            "log_level = \"DEBUG\"\nport = 9001\n",
        )
        .unwrap();
        assert_eq!(read_port(home.path(), None).unwrap(), 9001);
    }

    #[test]
    fn config_without_port_uses_the_default() {
        let home = temp_home();
        std::fs::write(home.path().join("config.toml"), "log_level = \"INFO\"\n").unwrap();
        assert_eq!(read_port(home.path(), None).unwrap(), DEFAULT_PORT);
    }

    #[test]
    fn env_port_wins_over_config_toml() {
        let home = temp_home();
        std::fs::write(home.path().join("config.toml"), "port = 9001\n").unwrap();
        let port = read_port(home.path(), Some(OsString::from("9100"))).unwrap();
        assert_eq!(port, 9100);
    }

    #[test]
    fn invalid_port_is_a_config_error_naming_its_source() {
        let home = temp_home();
        std::fs::write(home.path().join("config.toml"), "port = 70000\n").unwrap();
        let Err(DaemonError::Config { message }) = read_port(home.path(), None) else {
            panic!("expected a config error");
        };
        assert!(message.contains("config.toml"), "{message}");

        let Err(DaemonError::Config { message }) =
            read_port(home.path(), Some(OsString::from("abc")))
        else {
            panic!("expected a config error");
        };
        assert!(message.contains(PORT_ENV_VAR), "{message}");
    }

    #[test]
    fn malformed_config_toml_is_a_config_error() {
        let home = temp_home();
        std::fs::write(home.path().join("config.toml"), "port = [\n").unwrap();
        assert!(matches!(
            read_port(home.path(), None),
            Err(DaemonError::Config { .. })
        ));
    }

    #[test]
    fn token_is_read_and_trimmed() {
        let home = temp_home();
        std::fs::write(token_path(home.path()), "secret-token\n").unwrap();
        assert_eq!(
            read_token(home.path()).unwrap().as_deref(),
            Some("secret-token")
        );
    }

    #[test]
    fn missing_or_empty_token_file_reads_as_none() {
        let home = temp_home();
        assert_eq!(read_token(home.path()).unwrap(), None);
        std::fs::write(token_path(home.path()), "  \n").unwrap();
        assert_eq!(read_token(home.path()).unwrap(), None);
    }

    #[test]
    fn info_reports_port_and_token_presence_but_not_the_token() {
        let home = temp_home();
        std::fs::write(home.path().join("config.toml"), "port = 9002\n").unwrap();

        let missing = info(home.path(), None).unwrap();
        assert_eq!(missing.port, 9002);
        assert!(!missing.token_present);
        assert_eq!(
            missing.token_path,
            home.path().join("token").display().to_string()
        );

        std::fs::write(token_path(home.path()), "secret-token").unwrap();
        let present = info(home.path(), None).unwrap();
        assert!(present.token_present);
        let json = serde_json::to_string(&present).unwrap();
        assert!(!json.contains("secret-token"), "{json}");
    }

    #[test]
    fn api_url_targets_loopback_only() {
        assert_eq!(
            api_url(8765, "/api/health").unwrap(),
            "http://127.0.0.1:8765/api/health"
        );
        for path in [
            "/docs",
            "api/health",
            "/api/../docs",
            "/api/x?y=1",
            "/api/@evil.example",
            "//evil.example/api/",
            "/api/x#frag",
        ] {
            assert!(
                matches!(api_url(8765, path), Err(DaemonError::InvalidRequest { .. })),
                "{path} should be rejected"
            );
        }
    }

    #[test]
    fn errors_serialise_with_a_kind_tag() {
        let error = DaemonError::TokenMissing {
            path: "/x/token".into(),
        };
        let json = serde_json::to_value(&error).unwrap();
        assert_eq!(
            json,
            serde_json::json!({ "kind": "token_missing", "path": "/x/token" })
        );
    }
}
