# Decisions

Each entry is one decision and the reason for it. Add new entries at the bottom; to change one, add a new entry that supersedes it.

1. **Name: SpoolHQ** (Python package `spoolhq`, CLI `spool`). A spool feeds thread one turn at a time, as the loop feeds tickets; `spoolhq` was free as a package name and `spool` is short to type.
2. **UI: Tauri 2 + React + TypeScript.** Small native binaries on all three desktop platforms, with a mainstream, well-typed UI stack.
3. **Separate Python daemon (FastAPI).** Runs must survive closing the window, and the same daemon can run headless on a server.
4. **CLI: Typer.** Typed, minimal-boilerplate CLI that shares code and types with the daemon.
5. **Agent runtime: Claude Agent SDK behind an `AgentRunner` interface.** Use the best-supported coding agent now, without locking out other agents later.
6. **Storage: files for projects and tickets, SQLite for run history.** Specs and tickets stay readable and diffable in git; run history needs queries, not diffs.
7. **Stack templates: Copier.** It can both generate and later update projects from a template, which plain cookiecutter cannot.
8. **Only the planner, implementer and reviewer are LLM agents; everything else is plain code.** Gates, git, merging and tracker sync must be deterministic and testable.
9. **Local git first, GitHub optional.** The tool must work offline and without an account; GitHub adds pull requests on top.
10. **Licence: Apache-2.0.** Permissive, with an explicit patent grant, and compatible with the prior art we may borrow from.
11. **TypeScript pinned to 6.0.3, not 7.x.** typescript-eslint 8.71 supports TypeScript < 6.1; revisit when typescript-eslint supports 7.
12. **`.gitattributes` forces LF line endings.** Windows checkouts would otherwise get CRLF and fail the Prettier and ruff format checks.
13. **ruff's `S` (security) rules are on.** `shell=True` and similar unsafe calls are caught in CI rather than in review.
14. **`uv sync --locked` everywhere.** CI fails if `uv.lock` is out of date instead of silently re-resolving.
15. **The justfile's Windows shell is `powershell.exe`, not `pwsh`.** Windows PowerShell is always installed; PowerShell 7 is not.
16. **The GitHub repo is `ATOM43/spoolhq`.** It matches the package name, so there is one name to search for.
17. **The daemon binds to 127.0.0.1 only, with no override.** It runs agents on your code; nothing off the machine should reach it. A non-loopback `host` in config or env is a validation error.
18. **Local auth is a bearer token in `~/.spoolhq/token` (mode 0600, folder 0700).** Other local users and web pages cannot read it, and the CLI and desktop app need no login; it is compared with `secrets.compare_digest`.
19. **`GET /api/health` needs no token.** Clients use it to detect a running daemon, and it reveals nothing; every other `/api/*` route is protected by a middleware, so new routes are protected by default.
20. **Requests whose `Host` is not `127.0.0.1:<port>` or `localhost:<port>` get 400.** This blocks DNS-rebinding attacks from web pages, which send their own domain in `Host`.
21. **Logs are JSON lines from stdlib `logging` with a small formatter, no logging dependency.** One rotating file (10 MB × 5) that tools can parse; the token is redacted from every line as a backstop.
22. **Runtime dependencies are pinned exactly in `pyproject.toml`, like the dev tools.** SpoolHQ is an application, not a library; revisit if it is ever installed alongside other packages.
23. **The CLI's HTTP client ignores proxy environment variables (`trust_env=False`).** The daemon is always local; a user's `HTTP_PROXY` must not route CLI calls through a proxy.
