# SpoolHQ

SpoolHQ is an open-source, local-first desktop app that turns a written spec into a ticket plan, then has a coding agent implement the tickets one at a time, with tests and review before each merge. A Python daemon runs the loop, a `spool` CLI drives it, and a Tauri desktop app shows what is happening.

**Status: pre-alpha, not usable yet.** The daemon serves a minimal authenticated API, and the desktop app shows whether it is running; nothing else works yet.

## Development quickstart

Install [uv](https://docs.astral.sh/uv/), [Node.js 24 LTS](https://nodejs.org/), [pnpm](https://pnpm.io/) and [just](https://just.systems/), then:

```sh
just install && just test
```

## Run the daemon

```sh
uv run --directory daemon spool serve     # or: just dev
```

The daemon listens on `http://127.0.0.1:8765` only; the interactive API docs are at `/docs`. On first start it writes a random access token to `~/.spoolhq/token` (readable only by you); the `spool` CLI reads it from there, and every `/api/*` route except `/api/health` needs it as `Authorization: Bearer <token>`. Settings live in `~/.spoolhq/config.toml` (`port`, `log_level`) and can be overridden with `SPOOLHQ_PORT` and `SPOOLHQ_LOG_LEVEL`; set `SPOOLHQ_HOME` to use another folder. Logs are JSON lines in `~/.spoolhq/logs/daemon.log`.

`uv run --directory daemon spool version` prints the CLI's version and, if the daemon is running, the daemon's.

## Run the desktop app

The desktop app is a [Tauri 2](https://tauri.app/) window around a React UI. It finds the daemon through `~/.spoolhq/` (or `SPOOLHQ_HOME`) and shows whether it is reachable; it does not start the daemon itself.

### Prerequisites

Everything from the development quickstart, plus [Rust via rustup](https://rustup.rs/) (the toolchain version is pinned in `rust-toolchain.toml` and installed on first use) and your platform's packages:

- **Fedora**

  ```sh
  sudo dnf install webkit2gtk4.1-devel openssl-devel curl wget file \
    libappindicator-gtk3-devel librsvg2-devel libxdo-devel
  sudo dnf group install c-development
  ```

- **Ubuntu / Debian**

  ```sh
  sudo apt update
  sudo apt install libwebkit2gtk-4.1-dev build-essential curl wget file \
    libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev
  ```

- **macOS**: the Xcode Command Line Tools (`xcode-select --install`).
- **Windows**: [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) with "Desktop development with C++", and the WebView2 runtime (already installed on Windows 10 1803+ and Windows 11).

### Start it

```sh
just install
just dev        # starts the daemon and the app together; Ctrl-C stops both
```

`just daemon` and `just desktop` start either one alone. The top bar shows **Daemon ok · v…** when the daemon answers, **Reconnecting…** while it retries after losing it (every 3 s), and **Daemon not running** when nothing answers; in that case Home shows the `spool serve` command and a **Retry** button.

The access token never reaches the web view: the Rust side reads `~/.spoolhq/token` and adds it to each daemon request.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow and [DECISIONS.md](DECISIONS.md) for why things are the way they are.

## Licence

[Apache-2.0](LICENSE)
