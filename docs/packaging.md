# Packaging the daemon

The desktop app ships its own daemon: the whole `spool` CLI, `serve` included, built with PyInstaller as one file and declared as a Tauri sidecar. Closing the window hides it, a tray icon brings it back or quits ([below](#closing-quitting-and-the-tray)). Release tags build installers for every OS and a signed update feed ([Installers and updates](#installers-and-updates)).

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

`tauri-build` fails when an `externalBin` file is missing, even for `cargo clippy` or `cargo test`. The Rust workflow therefore runs `just sidecar-placeholder` first, which creates an empty `binaries/spoolhq-<triple>` if none exists and never overwrites a real binary. `just install` runs it too, so `just lint-rust` works right after cloning. An app built with the placeholder can't start a daemon: Home shows the daemon-missing state.

## How the app finds or starts the daemon

`desktop/src-tauri/src/sidecar.rs`, at launch:

1. Read the port and the token the way the CLI does (`SPOOLHQ_HOME`, `SPOOLHQ_PORT`, `config.toml`) and ask `GET /api/health` with the token.
2. A 200 with `{"status": "ok", "service": "spoolhq"}` is a SpoolHQ daemon: the app uses it and starts nothing. (`service` tells SpoolHQ apart from other apps; the `fastapi-react` template's own `/api/health` also says `{"status": "ok"}`.)
3. Nothing answers: start the `spoolhq` binary next to the app's executable (where Tauri puts `externalBin` files) with `serve`, no console window on Windows, then poll health for up to 15 s. Home shows "Starting SpoolHQ…" meanwhile.
4. Any other answer: start nothing. Home shows "Port 8765 is used by another program", with how to pick another port (`port` in `config.toml` or `SPOOLHQ_PORT`).
5. The binary can't start, exits during start, or doesn't answer within 15 s: Home shows the daemon-missing state with the log folder (`~/.spoolhq/logs`). A daemon that answers late is still picked up by the 3 s status poll.

The state goes to the webview through `daemon_info` (`launch`); the token stays in Rust and the CSP is unchanged. The app spawns the binary with `std::process`, so no shell plugin is needed and the webview can't start processes.

The one-file binary is a launcher with the daemon as its child, and the daemon starts agents. So the app starts the launcher on its own, never one process at a time:

- **Linux and macOS**: in its own process group (`process_group(0)`). Stopping it sends SIGTERM, and later SIGKILL, to the whole group with `kill -- -<pgid>` (an argument list; no shell, no `libc` dependency).
- **Windows**: inside a Job Object with kill-on-close (`windows-sys`). Ending the job ends every process in it, and so does the app exiting or crashing, since the app holds the job's only handle. No `taskkill`.

## Closing, quitting and the tray

**Closing the window hides it** while `keep_running` is on (the default). The app, the daemon (its own or an external one) and any run keep going, and the webview stays loaded, so the event bridge stays connected; reopening shows the current state with no gap (a dropped stream still resumes from the last `seq`). The setting is **Keep running when the window is closed** in Settings → General, saved through the daemon (`PUT /api/settings/desktop`) to `~/.spoolhq/config.toml`, which the app reads on every close:

```toml
[desktop]
keep_running = true
```

With it off, closing the window quits.

**The tray icon** has a menu:

- a status line, not clickable: "Running T05 · Implement", "Paused · usage limit", "Paused", "Idle" or "Daemon stopped", refreshed every 3 s; with an external daemon it adds "external daemon, keeps running after Quit";
- **Open SpoolHQ**, which shows and focuses the window (a left click on the icon does too on Windows and macOS; Linux tray hosts only open the menu);
- **Quit**.

**GNOME** shows tray icons only with an AppIndicator extension, such as *AppIndicator and KStatusNotifierItem Support* (`gnome-shell-extension-appindicator` on Fedora and Ubuntu). Without one there is no icon: start SpoolHQ again to show the hidden window (a second launch only focuses the first, through Tauri's single-instance plugin), and quit with **Quit SpoolHQ** in Settings → General or by turning Keep running off and closing the window. On macOS, clicking the Dock icon also shows the window.

**Quitting** (the tray's Quit, Settings → General, the app menu or Cmd+Q, or closing with Keep running off):

| Daemon | What happens |
| --- | --- |
| Started by the app, a run going | A confirm: "A run is going (T05). Quit stops it; the ticket goes back to Ready." (**Quit** · **Keep running**; closing the dialog keeps running). Then as below. |
| Started by the app, idle | `POST /api/shutdown` ([API](api.md#shutdown)): the daemon cancels each run like Cancel (marked `cancelled`, worktree removed), closes the event streams and exits. The app waits up to 15 s for the launcher to end, then kills the group or job; it kills the group or job in any case afterwards, so no stray child is left. If the request fails, it sends SIGTERM to the group first (Unix). |
| External (`spool serve`) | The app quits; the daemon and any run keep going. No confirm. |

If the app exits any other way while it still owns a daemon, it stops the group (SIGTERM, a kill after 5 s); on Windows the Job Object ends it regardless.

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

## Installers and updates

### One version

The daemon package (`daemon/pyproject.toml`), `desktop/package.json` and `desktop/src-tauri/tauri.conf.json` carry the same version. Change it with:

```sh
just set-version 0.1.0
```

which writes all three (`scripts/release.py set-version`) and relocks the daemon (`uv lock`). The release fails with "Tag v0.1.0 doesn't match the app version 0.0.9" when the tag isn't `v<version>`, and with "The app versions differ: …" when the files disagree.

### Making a release

1. `just set-version 0.1.0`, commit and push.
2. Tag with the release notes as the message and push the tag: `git tag -a v0.1.0 -m "First release" && git push origin v0.1.0`.
3. `.github/workflows/release.yml` builds every installer and `latest.json` and creates a **draft** GitHub Release with them. Check it, then publish it on GitHub. Until then, the feed's `latest/download/latest.json` still points at the previous published release.

A **dry run** (Actions → Release → Run workflow, `dry_run` ticked, the default) builds and checks everything on any branch and uploads the installers and `latest.json` as workflow artifacts only; it makes no release and doesn't check the tag.

The signing secrets are needed for a dry run too. Before your public key is in `tauri.conf.json`, `tauri build` refuses to sign, so give the dry run the public key that matches the secrets in its `pubkey` input (`gh workflow run release.yml -f dry_run=true -f pubkey="$(cat key.pub)"`); the input is ignored outside dry runs.

### What gets built

| OS | Runner | Installers | Update artifact |
| --- | --- | --- | --- |
| Linux x86_64 | `ubuntu-latest` | AppImage, `.deb`, `.rpm` | the AppImage |
| Windows x86_64 | `windows-latest` | NSIS `SpoolHQ_<v>_x64-setup.exe` | the setup `.exe` |
| macOS arm64 | `macos-26` | `SpoolHQ_<v>_aarch64.dmg` | `SpoolHQ_<v>_aarch64.app.tar.gz` |
| macOS x86_64 | `macos-26-intel` | `SpoolHQ_<v>_x64.dmg` | `SpoolHQ_<v>_x86_64.app.tar.gz` |

Each job first builds the real sidecar for its OS (`just build-daemon`, with the dev-tools check), then the Tauri bundle (`tauri build --bundles …`), so no installer can hold the placeholder. Then it checks its bundles: the sidecar is in the `.deb` and `.rpm` file lists; the AppImage is extracted, the `.dmg` mounted and the Windows installer run silently (`/S /D=<temp>`), and the T23 smoke test runs against the `spoolhq` binary inside; and its `latest-<platform>.json` lists the platform with a URL and a signature. A last job merges the four into `latest.json`, checks all four platforms again and publishes (or, for a dry run, uploads).

The Linux build runs on Ubuntu 24.04, so the AppImage needs glibc 2.39 or newer.

### The update feed

The app carries Tauri's updater plugin (`tauri-plugin-updater`, pinned 2.14.1), registered in Rust only: the webview has no updater permission. T52 adds the update check and the Install and restart button. `tauri.conf.json` holds the feed and the public key:

```json
"plugins": {
  "updater": {
    "pubkey": "<the public key>",
    "endpoints": ["https://github.com/ATOM43/Spoolhq/releases/latest/download/latest.json"]
  }
}
```

`bundle.createUpdaterArtifacts` makes `tauri build` sign each update artifact with `TAURI_SIGNING_PRIVATE_KEY` (a `.sig` file next to it). `latest.json`, built by `scripts/release.py`:

```json
{
  "version": "0.1.0",
  "notes": "First release",
  "pub_date": "2026-11-23T10:00:00Z",
  "minimum_version": "",
  "platforms": {
    "linux-x86_64": { "url": "https://github.com/ATOM43/Spoolhq/releases/download/v0.1.0/SpoolHQ_0.1.0_amd64.AppImage", "signature": "<the .sig file>" },
    "windows-x86_64": { "url": "…/SpoolHQ_0.1.0_x64-setup.exe", "signature": "…" },
    "darwin-aarch64": { "url": "…/SpoolHQ_0.1.0_aarch64.app.tar.gz", "signature": "…" },
    "darwin-x86_64": { "url": "…/SpoolHQ_0.1.0_x86_64.app.tar.gz", "signature": "…" }
  }
}
```

`minimum_version` is empty for now; T52 reads it but v0.1.0 doesn't enforce it. The notes are the tag's message (`SpoolHQ v0.1.0` for a tag without one). The workflow also checks that each signature was made by the key whose public half is in `tauri.conf.json` (the minisign key ids match), so a release signed with the wrong key fails instead of shipping updates no install accepts.

**Linux updates go through the AppImage only.** The updater replaces the running AppImage. Someone who installed the `.deb` or `.rpm` installs the new package from the release page (or their package manager) instead; T52's notice tells them so.

### The signing key

The update signing key is yours: CI only reads it from GitHub secrets, and it is never committed, printed or logged. Set it up once:

1. Generate the key pair locally, with a password, outside the repository:

   ```sh
   pnpm --dir desktop exec tauri signer generate -w ~/.tauri/spoolhq.key
   ```

   This writes the private key to `~/.tauri/spoolhq.key` and the public key to `~/.tauri/spoolhq.key.pub`.
2. Add two repository secrets (Settings → Secrets and variables → Actions, or `gh secret set`): `TAURI_SIGNING_PRIVATE_KEY` with the contents of `spoolhq.key`, and `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` with its password. `gh secret set TAURI_SIGNING_PRIVATE_KEY < ~/.tauri/spoolhq.key` reads the file without it showing in your shell history.
3. Put the contents of `spoolhq.key.pub` (one base64 line) in `plugins.updater.pubkey` in `tauri.conf.json` and commit it. A tag fails with "Put the update public key in tauri.conf.json; see docs/packaging.md" while it is empty.
4. Back the private key and its password up outside GitHub (a password manager, an offline copy). GitHub secrets can't be read back.

> **Losing the private key or its password means installed copies can't trust any new update.** Each install only accepts updates signed by the key it shipped with; a new key reaches users only through a manual reinstall.

Without the secrets the workflow stops at once with "Set the TAURI_SIGNING_PRIVATE_KEY secret; see docs/packaging.md" (or the same for `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`). A local `pnpm --dir desktop tauri build` needs the same two variables, since update artifacts are always signed.

### Unsigned builds

Neither the apps nor the installers are code signed or notarized yet; that comes later. The macOS app is only ad-hoc signed (`bundle.macOS.signingIdentity: "-"`), which Apple Silicon needs to run it at all.

- **macOS**: opening a downloaded unsigned app shows "SpoolHQ can't be opened" or "is damaged". Drag it to Applications, then either right-click → Open → Open, allow it under System Settings → Privacy & Security → **Open Anyway**, or remove the quarantine attribute: `xattr -dr com.apple.quarantine /Applications/SpoolHQ.app`.
- **Windows**: SmartScreen shows "Windows protected your PC". Click **More info** → **Run anyway**. The installer installs for the current user (no admin prompt).
- **Linux**: make the AppImage executable (`chmod +x SpoolHQ_*.AppImage`); the `.deb` and `.rpm` install as usual.

Binaries built locally aren't quarantined.
