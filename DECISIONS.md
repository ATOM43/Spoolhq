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
24. **The daemon token stays in Rust.** The web view calls only the Rust commands `daemon_info` (port and whether a token exists) and `daemon_get` (status and body); Rust reads `~/.spoolhq/token` on each request and adds the `Authorization` header. Script in the web view can never read or leak the token, and the daemon needs no CORS.
25. **No HTTP plugin; the scope lives in the command.** `daemon_get` only builds `GET http://127.0.0.1:<port>/api/...` URLs from a character-checked path, and its client ignores proxy variables. The window's one capability grants just the two app commands (no `core:default`), via permissions generated from `build.rs`.
26. **Strict CSP.** Scripts, styles, fonts and images from `'self'` only, `connect-src` limited to Tauri IPC, `object-src`/`base-uri`/`form-action`/`frame-ancestors` `'none'`, plus `freezePrototype`. Tauri injects it into the built app; the Vite dev server in `pnpm tauri dev` is not covered.
27. **Settings uses the native `<dialog>`, not Radix Dialog.** Radix's scroll lock injects a `<style>` element, which `style-src 'self'` blocks; `<dialog>` traps focus and closes on Escape on its own.
28. **Fonts are bundled with `@fontsource`, no CDN.** Inter (400/500/600) and JetBrains Mono (400) ship as files (`assetsInlineLimit: 0`), so the app works offline, makes no third-party requests, and the CSP can stay `font-src 'self'`.
29. **shadcn/ui components use SpoolHQ's token names** (`bg-surface`, `text-ink-muted`, `bg-accent`, …) instead of shadcn's (`primary`, `muted`, `accent`), because shadcn's `accent` is a hover grey that clashes with our accent blue. They were copied from the new-york-v4 source and restyled.
30. **Status rules.** Health (no token) is checked before version, so a stopped daemon reads as "not running" even without a token file. A daemon that was reachable shows "Reconnecting…" for up to three failed checks (about 9 s), then "Daemon not running"; one that never answered is "not running" at once. Token, 401, 400 and other failures show a fourth state, "Daemon error", with the reason on Home.
31. **The app reads the port like the daemon:** `SPOOLHQ_PORT`, then `port` in `config.toml`, then 8765. Port and token are re-read on every check, so starting the daemon after the app needs no restart.
32. **Rust is pinned like the rest:** toolchain 1.99.1 in `rust-toolchain.toml`, crates with `=` versions, and `--locked` in the justfile. CI installs the toolchain with the runner's own rustup rather than a third-party action, and does not cache Rust builds yet.
33. **`@tanstack/react-query` is pinned to 5.104.3, not 5.104.4.** pnpm 12's minimum release age rejected the day-old 5.104.4; we pin an older release instead of exempting packages from the policy.
34. **Backend layering: `core` → `services` → `api`/`cli`, enforced by import-linter.** Routers and commands stay thin and call services; services never import FastAPI, Starlette, Typer or uvicorn, so the same logic serves HTTP, the CLI and tests; `core` (config, token, logging) depends on nothing above it. The contracts live in `daemon/pyproject.toml` and run in `just lint`, so a wrong import fails CI.
35. **Frontend: Feature-Sliced Design, enforced by lint.** `desktop/src/` is split into app, pages, widgets, features, entities and shared; slices expose an `index.ts`, import only from lower layers and never from a sibling slice. `eslint-plugin-boundaries` 7 checks this in `just lint`. We chose it over Steiger (the FSD project's own linter) because it runs inside ESLint, which we already run, and does not flag our deliberately empty placeholder slices.
36. **`core/logs.py` keeps its name** rather than becoming `core/logging.py`, so it never shadows the standard library's `logging` module.
37. **Design tokens live in `shared/styles/tokens.css`;** `app/styles/global.css` imports them with Tailwind, the fonts and the base layer.
38. **`unrs-resolver`'s install script is not run** (`allowBuilds` in `desktop/pnpm-workspace.yaml`). `eslint-import-resolver-typescript`, which lets the boundaries rules resolve `@/` imports, gets its native binary from an optional prebuilt package; the script is only a fallback.
