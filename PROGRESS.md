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
