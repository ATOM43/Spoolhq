# Contributing to SpoolHQ

Thanks for helping. SpoolHQ is pre-alpha, so expect things to move.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 for you if needed)
- [Node.js](https://nodejs.org/) 24 LTS
- [pnpm](https://pnpm.io/) — the exact version is pinned in `desktop/package.json` (`packageManager`)
- [just](https://just.systems/)
- [Rust](https://rustup.rs/) via rustup — the toolchain is pinned in `rust-toolchain.toml`
- Tauri's system packages for your platform — see [Run the desktop app](README.md#run-the-desktop-app)
- git

Linux, macOS and Windows are all supported. On Windows, `just` runs recipes in PowerShell.

## Commands

| Command | What it does |
| --- | --- |
| `just install` | Installs Python and Node dependencies exactly as locked |
| `just lint` | ruff, ruff format check, mypy, import-linter, the 500-line limit on source files (`scripts/check_line_limit.py`), ESLint (including the Feature-Sliced Design boundaries), Prettier check, `tsc --noEmit`, `cargo fmt --check`, `cargo clippy -- -D warnings` |
| `just test` | pytest and Vitest with coverage (daemon floor 85%), and `cargo test` — see [docs/testing.md](docs/testing.md) |
| `just dev` | Starts the daemon (`spool serve`) and the desktop app (`pnpm tauri dev`) |
| `just daemon` / `just desktop` | Starts only one of them |

Run `just lint && just test` before you push.

## Workflow

- Work is planned as tickets with IDs like `T07`.
- **Work on `main`.** No branches and no pull requests: commit each finished ticket to `main` and push.
- Keep each commit inside its ticket's scope, and check the ticket's "Done when" list before you push.
- **CI must pass** on Linux, macOS and Windows; if a push turns it red, fix it with a follow-up commit on `main`.
- Never force-push `main`.
- Code goes where [docs/architecture.md](docs/architecture.md) says; `just lint` enforces the layer rules.
- No source file over 500 lines (tests are exempt); split it along its responsibilities. An exception goes in `ALLOWED` in `scripts/check_line_limit.py`, with the reason.
- Commit in small, logical steps with clear messages.
- Never commit secrets, tokens or machine-specific paths.

## Licence

By contributing you agree that your contributions are licensed under the [Apache-2.0 licence](LICENSE).
