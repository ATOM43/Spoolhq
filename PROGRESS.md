# Progress

Newest entries at the bottom. One entry per merged ticket.

## T01 · Repository and tooling

- Monorepo layout: `daemon/` (Python package `spoolhq`, uv, src layout), `desktop/` (TypeScript package `@spoolhq/desktop`, pnpm), `templates/`, `docs/`.
- Python tooling: ruff (lint and format), mypy strict on `daemon/src`, pytest; Python 3.12+.
- TypeScript tooling: ESLint flat config with typescript-eslint, Prettier, Vitest, `tsc --noEmit`; Node 24 LTS, pnpm pinned via `packageManager`.
- `justfile` with `install`, `lint`, `test` and a placeholder `dev`, working on Linux, macOS and Windows.
- GitHub Actions CI on Linux, macOS and Windows, with pinned action SHAs and uv/pnpm caching.
- Contributor docs, issue forms, PR template, Apache-2.0 licence, and the decision log.
- Only placeholders exist: `spoolhq.__version__` and `appName()`, each with one test. No application code yet.

## T01 follow-ups

- Planning docs (`task.md`, `Plan.md`) renamed from the working name "orch" / "Agent Orchestrator" to SpoolHQ: CLI `spool`, paths under `~/.spoolhq/` and `~/spoolhq-projects/`.
- GitHub repo renamed from `ATOM43/Spool` to `ATOM43/spoolhq`.
- T01 tooling decisions recorded in `DECISIONS.md` (entries 11–16).

## T02 · Daemon and CLI scaffold

- `spoolhq.config`: home folder `~/.spoolhq/` (or `SPOOLHQ_HOME`), settings from `config.toml` then `SPOOLHQ_*` env (`host` fixed to 127.0.0.1, `port` 8765, `log_level` INFO); errors name the field and its source.
- `spoolhq.auth`: token from `secrets.token_urlsafe(32)` in `~/.spoolhq/token` (0600, folder 0700), created once and reused.
- `spoolhq.api`: `create_app(settings)` with `GET /api/health` (public) and `GET /api/version` (token). `LocalOnlyMiddleware` rejects foreign `Host` headers (400) and untokened `/api/*` calls (401). `/docs` and `/openapi.json` are served.
- `spoolhq.logs`: JSON-lines logging to `~/.spoolhq/logs/daemon.log` (rotating 10 MB × 5), uvicorn routed through it, plain text on stderr when interactive, token redacted.
- `spoolhq.cli`: Typer app `spool` with `serve [--port]` and `version`; `ApiClient` (httpx) reads the port from settings and the token from the token file. Also runnable as `python -m spoolhq`.
- `just dev` runs `spool serve`.
- Tests cover health, auth, Host check, token file, config precedence and errors, host refusal, log format, the CLI without a daemon, and an integration test (`-m integration`) that starts the real server in a subprocess.

## T03 · Desktop shell

- `desktop/` is a Tauri 2 + React 19 + Vite 8 + TypeScript app (identifier `dev.spoolhq.app`, window "SpoolHQ", 1440×900, minimum 1100×700), keeping ESLint (now with React Hooks and React Refresh rules), Prettier, Vitest and `tsc`.
- Rust (`desktop/src-tauri/`): `daemon_info` returns `{ port, token_present, token_path }` from `SPOOLHQ_HOME`/`~/.spoolhq` (`SPOOLHQ_PORT`, `config.toml`, default 8765); `daemon_get` performs `GET 127.0.0.1:<port>/api/...` and adds the token. The web view never sees the token. Strict CSP, one capability with only these two commands.
- Typed client in `desktop/src/api/`: `getHealth()`, `getVersion()`, `getDaemonInfo()`; failures are `DaemonError`s of kind `not_running`, `token_missing`, `unauthorized` (401), `bad_host` (400), `http`, `invalid_response`, plus `config` and `internal`.
- Shell with React Router: `/` Home (daemon status, "No projects yet", Settings dialog placeholder), `/p/:id` project panel with Spec · Tickets · Run placeholder tabs. Top bar with the status pill ("Daemon ok · v…" / "Reconnecting…" / "Daemon not running" / "Daemon error"), polled every 3 s via TanStack Query.
- Daemon down: Home says "The daemon isn't running" with a copyable `spool serve` and Retry; a missing token names the file.
- Tailwind 4 design tokens (light and dark from the system), radius 4/6/8 px, 4 px spacing; shadcn/ui Button, Card, Tabs; Inter and JetBrains Mono bundled via `@fontsource`.
- `just dev` runs the daemon and `pnpm tauri dev` in parallel (`just daemon` / `just desktop` for one); `just lint` adds `cargo fmt --check` and `cargo clippy -D warnings`; `just test` adds `cargo test`. CI installs Rust and Tauri's Linux packages; no installers are built.
- Tests: client error mapping, status rules, status pill states, daemon-down and token-missing panels, routes (Vitest, Tauri mocked); port/token reading and URL restriction (Rust, temp `SPOOLHQ_HOME`). None needs a daemon or a window.
