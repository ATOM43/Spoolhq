# Packaging the daemon

The desktop app ships its own daemon: the whole `spool` CLI, `serve` included, built with PyInstaller as one file and declared as a Tauri sidecar. Closing the window and the tray come with T49; installers and release builds with T50.

## Building the binary

```sh
just build-daemon
```

This runs `scripts/build_sidecar.py` with the `build` dependency group (`pyinstaller==6.22.3`, build only; `just install` doesn't install it). It writes `desktop/src-tauri/binaries/spoolhq-<target triple>` (`.exe` on Windows), the name Tauri's `externalBin` expects, and prints its size. The folder is git-ignored. `--target <triple>` names another triple; PyInstaller can't cross-compile, so each OS builds its own.

What goes in:

- Everything `spoolhq/__main__.py` imports. PyInstaller follows imports inside functions too, so the CLI's lazy imports are found.
- Package data: `spoolhq/templates/` (the built-in `fastapi-react` template) and `spoolhq/services/context/prompts/`. Both are read through `importlib.resources`, which works from the binary.
- `uvicorn`'s submodules (it picks its protocol and loop modules by name), Copier's default Jinja extension `jinja2_ansible_filters` (loaded by name; without it every template fails) and `keyring`'s metadata.

What stays out:

- `spoolhq.devtools` and its scenarios (`--exclude-module`). After building, the script lists the binary's contents with PyInstaller's archive viewer and fails if any entry names `spoolhq.devtools` or `spoolhq/devtools`.
- The test fixtures (`daemon/tests/` isn't part of the package).
- The Claude Code CLI the Agent SDK wheel carries in `claude_agent_sdk/_bundled/` (315 MB). PyInstaller doesn't collect it, so the packaged `claude-agent-sdk` backend uses `claude` on `PATH`, as it does when `_bundled/` is missing (`spool agents` shows "PATH Claude Code").

The packaged daemon refuses `SPOOLHQ_DEV_FAKE_RUNNER` with `SPOOLHQ_DEV_FAKE_RUNNER is for development only` (it checks `sys.frozen`).

Sizes (PyInstaller 6.22.3, Python 3.12):

| OS | Size |
| --- | --- |
| Linux x86_64 | 35.1 MB (35.2 MB on CI) |
| macOS arm64 | 29.7 MB |
| Windows x86_64 | 31.5 MB |

### Smoke test

`scripts/smoke_sidecar.py <binary>` runs the built binary on a temp home, a temp projects folder and a free port: `version`; `serve` with `SPOOLHQ_DEV_FAKE_RUNNER=happy` must exit with the dev-only error; `serve`, then `GET /api/health` and `GET /api/version` with the token; `init` of an empty-repo project and of a `fastapi-react` project (with `git --version` as its commands); `tickets new` and `prompt show`, which renders the implementer prompt from the bundled prompt files.

```sh
uv run --directory daemon python ../scripts/smoke_sidecar.py ../desktop/src-tauri/binaries/spoolhq-x86_64-unknown-linux-gnu
```

### CI

`.github/workflows/package.yml` runs `just build-daemon` and the smoke test on Linux, macOS and Windows, on pushes to `daemon/**`, the two scripts and the workflow itself, and on `v*` tags (GitHub doesn't apply path filters to tag pushes).

`tauri-build` fails when an `externalBin` file is missing, even for `cargo clippy` or `cargo test`. The Rust workflow therefore runs `just sidecar-placeholder` first, which creates an empty `binaries/spoolhq-<triple>` if none exists and never overwrites a real binary. Run it, or `just build-daemon`, once on a fresh clone before `just lint-rust`. An app built with the placeholder can't start a daemon: Home shows the daemon-missing state.

## How the app finds or starts the daemon

`desktop/src-tauri/src/sidecar.rs`, at launch:

1. Read the port and the token the way the CLI does (`SPOOLHQ_HOME`, `SPOOLHQ_PORT`, `config.toml`) and ask `GET /api/health` with the token.
2. A 200 with `{"status": "ok", "service": "spoolhq"}` is a SpoolHQ daemon: the app uses it and starts nothing. (`service` tells SpoolHQ apart from other apps; the `fastapi-react` template's own `/api/health` also says `{"status": "ok"}`.)
3. Nothing answers: start the `spoolhq` binary next to the app's executable (where Tauri puts `externalBin` files) with `serve`, no console window on Windows, then poll health for up to 15 s. Home shows "Starting SpoolHQ…" meanwhile.
4. Any other answer: start nothing. Home shows "Port 8765 is used by another program", with how to pick another port (`port` in `config.toml` or `SPOOLHQ_PORT`).
5. The binary can't start, exits during start, or doesn't answer within 15 s: Home shows the daemon-missing state with the log folder (`~/.spoolhq/logs`). A daemon that answers late is still picked up by the 3 s status poll.

The state goes to the webview through `daemon_info` (`launch`); the token stays in Rust and the CSP is unchanged. The app spawns the binary with `std::process`, so no shell plugin is needed and the webview can't start processes.

A daemon the app started is stopped when the app exits: SIGTERM, then a kill after 5 s (on Windows, a kill; whether the launcher's child goes with it is unchecked there). SIGTERM matters because the one-file binary is a launcher with the daemon as its child: SIGKILL would leave the child running, while SIGTERM is passed on. A daemon the app found running is left alone. T49 changes this.

## Agent CLIs from a desktop launch

An app started from a desktop menu or Finder gets a short `PATH`, so `claude` or `codex` may be missing. `spool serve` (and `spool agents`, so it shows what the daemon would find) appends these folders to its `PATH` when they exist and aren't already on it, in this order:

- `~/.local/bin`, `~/.npm-global/bin`, `~/.bun/bin`, `~/.cargo/bin`
- `/opt/homebrew/bin`, `/usr/local/bin` (not on Windows)
- `%APPDATA%\npm` (Windows only)
- each folder in `extra_path` from `~/.spoolhq/config.toml`:

```toml
extra_path = ["~/tools/bin", "/opt/agents/bin"]
```

The user's shell is never run to read its `PATH`. Agents inherit the extended `PATH` through the environment allowlist. `spool agents` prints the full path each CLI was found at (`path       /home/me/.local/bin/claude`).

## macOS: unsigned builds

The binary and the app aren't signed or notarized yet; signing comes later, after T50. On macOS, Gatekeeper may block an unsigned binary that was downloaded: allow it under System Settings → Privacy & Security, or remove the quarantine attribute with `xattr -d com.apple.quarantine <file>`. Binaries built locally aren't quarantined.
