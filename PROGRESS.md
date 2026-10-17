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
