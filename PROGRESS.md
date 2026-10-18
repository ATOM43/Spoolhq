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

## Restructure (before T04)

Structure only; no routes, commands, UI or security rules changed.

- Backend: `config`, `auth` and `logs` moved to `spoolhq/core/`; the API split into `api/routers/` (`health.py`, `version.py`) and `api/schemas/` (Pydantic `Health`, `Version`); empty `services/` packages for projects, tickets, scheduler, runs, git, agents, gates and tracker; `cli/` unchanged apart from imports.
- import-linter (dev only) checks three contracts — the layers, `core` importing nothing above it, and services free of FastAPI/Starlette/Typer/uvicorn — in `just lint`.
- Frontend: Feature-Sliced Design under `desktop/src/` — `app/` (entry, Query provider, router, global styles), `pages/home` and `pages/project-panel`, `widgets/top-bar` and `widgets/daemon-down-panel`, `features/daemon-status` and `features/open-settings`, `entities/daemon` (plus empty `project`, `ticket`, `run`), and `shared/` (`api`, `ui`, `lib`, `config`, `styles`). Every slice has an `index.ts`; tests sit next to their code.
- `eslint-plugin-boundaries` (dev only) enforces public-API-only, downward-only and no-sideways imports in `just lint`.
- Docs: `docs/architecture.md`; "Code structure" in `CLAUDE.md`; work directly on `main` (no branches or pull requests) in `CLAUDE.md` and `CONTRIBUTING.md`.

## T04 · Project workspace and settings

- `projects_dir` setting in `core/config` (default `~/spoolhq-projects`, `config.toml` or `SPOOLHQ_PROJECTS_DIR`, `~` expanded).
- `services/projects/`: Pydantic model of `project.yaml` (`name`, `repo`, `default_branch`, `template`, `commands`, `agents`, `limits`, `merge_policy`, `git.remote`, `tracker`) with `extra="forbid"` throughout; the repo must be a git work tree and the branch must exist. Every error at once as `project.yaml: <dotted.path>: <message>` (unknown keys suggest the closest field); YAML syntax errors give line and column.
- ruamel.yaml round-trip loading and saving (`load_project`, `save_project`): comments and formatting survive, only changed values are rewritten, writes are atomic.
- `services/git/`: read-only `is_work_tree` and `branch_exists` (`git -C <repo> rev-parse …`, argument lists only).
- `spool init <name> --repo <path> [--branch] [--remote]` creates `project.yaml` (defaults plus placeholder `just` commands), `CONTEXT.md` (Objective, Background, Requirements, Deliverables), `tickets/` and `runs/`, atomically; refuses an existing folder and bad input without creating anything; notes missing `PROGRESS.md` / `DECISIONS.md` / `CLAUDE.md` in the repo without writing them.
- `spool project validate <name>` prints `valid` or every error, exiting 1 on errors.
- Docs: "Projects" in `docs/architecture.md`, `docs/project-yaml.md`, DECISIONS 39–43.
- Tests: init then validate, each required field missing, documented messages for bad values (remote, backend, budget, retries, typos, slugs), repo/branch refusals that create nothing, existing folder, failures mid-init, comment-preserving round-trip, YAML line/column, unsafe tags. Temp `SPOOLHQ_HOME`, `SPOOLHQ_PROJECTS_DIR` and git repos in fixtures.

## T05 · Ticket file format and store

- `services/tickets/`: one markdown file per ticket in `<workspace>/tickets/`, named `<id>-<slug>.md`. Pydantic model of the frontmatter (`id`, `title`, `phase`, `depends_on`, `status`, `estimate_h`, `review_required`, `tracker_ref`), strict and with `extra="forbid"`; the id must match the file-name prefix, no self or duplicate dependencies. Every error at once as `tickets/<file>: <field>: <message>`; YAML errors give the file's line and column.
- Byte-identical round-trip: the body is kept as raw text; saving rewrites only the frontmatter lines of changed keys (comments, quoting, list layout, line endings, final newline, BOM kept), with an atomic write.
- Done-when parsing (read-only): `[{text, checked}]` from the `## Done when` section; a missing or empty section is a warning.
- Store API: `list_tickets(project, status=, phase=)` (sorted by id, invalid files reported without stopping the rest), `load_ticket`, `save_ticket`, `TicketError` / `TicketValidationError`.
- CLI: `spool tickets list <project> [--status] [--phase]` (exit 1 if any file is invalid), `spool tickets show <project> <id>`, `spool tickets edit <project> <id>` ($VISUAL / $EDITOR via `shlex.split` as an argument list, re-validation, reopen or restore from a backup). Shared CLI helpers moved to `cli/common.py`.
- Fixtures: round-trip files (comments, CRLF, no final newline, unicode, extra sections, block and flow lists, quoting, BOM, frontmatter only) and the 18-ticket dashboard plan.
- T04 leftovers: `git.remote` follows GitHub's owner and repository naming rules; the README quickstart covers `spool init` and `spool tickets`.
- Docs: `docs/ticket-format.md`, "Tickets" in `docs/architecture.md`, DECISIONS 45–51.

## T06 · Dependency graph and scheduler

- `services/scheduler/`: `validate_plan(tickets)` reports unknown dependencies, each distinct cycle (members in work order, from the lowest id) and ids defined in several files, all at once, as `PlanProblem(code, ticket_ids, message)`. Ids sort by number (`T99` before `T100`).
- Status transitions: the `TRANSITIONS` table is the single source; `check_transition` raises `TransitionError` (`blocked → done is not allowed`, `T07 cannot start: waits for T04, T06`), same status is a no-op; `apply_transition(project, id, status)` saves through the T05 store, changing only the `status` line.
- Scheduling: `next_ready`, `waiting_on`, and `explain_idle` with the reasons `all_done`, `running`, `awaiting_approval`, `blocked`, `waiting`, `plan_not_approved`. All refuse an invalid plan with `PlanError`.
- Progress: `remaining_hours`, `critical_path` (longest not-done chain by hours, ties to lower ids, decimal sums) and `summary` (counts per status, hours, path).
- CLI: `spool plan check|next|summary <project>` (new `cli/plan.py`) and `spool tickets set-status <project> <id> <status>`; non-zero exit on problems or refused moves.
- Docs: `docs/scheduler.md`, "Scheduler" in `docs/architecture.md`, README commands, DECISIONS 52–57.
- Tests: validation (unknown dep, 3-ticket cycle, separate and overlapping cycles, duplicates, numeric order), every allowed and disallowed transition, same-status no-op, dependency rule, status-line-only saves, the dashboard's next-ready order, remaining hours and critical path, one test per idle reason, and the CLI output and exit codes.

## Fixes

- git: SpoolHQ's git calls never run repository hooks (`-c core.hooksPath=<home>/hooks-disabled`, which must stay empty) and never sign (`commit.gpgsign`, `tag.gpgsign`, `tag.forceSignAnnotated` all false), closing a sandbox escape through a tracked hooks folder the agent can edit and a hang on signing prompts (DECISIONS 84–85).
- CLI forces UTF-8 on stdout/stderr: `spool` no longer crashes with `UnicodeEncodeError` on Windows when output is redirected (`spool plan check > out.txt`); the console script now points at `spoolhq.cli:main`, which reconfigures the streams before Typer runs (DECISIONS 58). Subprocess tests run the real CLI with `PYTHONIOENCODING=cp1252`.

## Chores

- graph: Graphify 0.9.92 code graph committed in `graphify-out/` (`GRAPH_REPORT.md`, `graph.json`, `graph.html`), with a "Code graph" section in `CLAUDE.md` (DECISIONS 86).
- tests: daemon tests moved (`git mv`) into folders mirroring `src/spoolhq/`, `services/git` fixtures in their own `conftest.py`, `FIXTURES_DIR` for shared data, `tests/test_layout.py` guarding the layout; 570 → 573 tests, no test logic changed (DECISIONS 87).
- audit: interrupted runs keep their worktrees, `~/.claude`, `~/.claude.json` and `CLAUDE_CONFIG_DIR` are denied to the agent's commands, `default_branch` must be a branch name, the event bus starts at the last stored id, the run summary keeps the end of the final message, proxy and CA variables reach `claude`, `spool serve --port` is gone, the CLI names a non-SpoolHQ server, Ctrl-C in `spool tickets edit` restores the file, shared helpers have one copy, and the stop sequence is tested (DECISIONS 118–126).

## T07 · Run log and event bus

- `services/runs/`: the run log in `<workspace>/.spoolhq/state.db` (stdlib `sqlite3`, WAL, `synchronous=NORMAL`, foreign keys, 5 s busy timeout, one locked connection per `RunLog`, `BEGIN IMMEDIATE` per operation). Schema v1 (`runs`, `attempts`, `events`, append-only triggers, indexes) via `PRAGMA user_version` migrations; newer schemas and non-SQLite files are refused with the documented messages.
- `RunLog`: `start_run`, `set_run_status` (terminal statuses set `ended_at`, ended runs can't change), `start_attempt` (per-ticket numbers and `runs/<ticket>/<NNN>/` folders), `finish_attempt`, `record_usage` (tokens and micro-USD cost), `append_event` (JSON dicts up to 64 KiB), reads (`get_run`, `list_runs`, `list_attempts`, `run_usage`, `events_since`). Lifecycle events are written in the same transaction and published only after commit, in id order. `StrEnum`s for statuses and kinds, frozen dataclasses for results, UTC millisecond timestamps from an injectable clock.
- Attempt files: `write_artifact` (atomic) for `transcript.jsonl`, `gates.json`, `diff.patch`, `review.json` only; `append_transcript` (fsynced JSON lines); `attempt_files` resolves the row's `dir` and refuses one outside `runs/`.
- `EventBus`: synchronous, thread-safe fan-out with bounded per-subscriber queues, `run_id` filter, `lagged` + `last_id` for resync from `events_since`, optional `notify` callback; failing subscribers are isolated.
- Crash recovery: `recover_interrupted` marks other instances' `running`/`paused` runs and their running attempts `interrupted` in one transaction, one `run.interrupted` event each, idempotent.
- Daemon: `spool serve` takes the single-instance lock `~/.spoolhq/daemon.lock` (`fcntl.flock` / `msvcrt.locking`, pid in the file) before uvicorn starts; the lifespan generates a `daemon_instance`, opens a `RunLog` + `EventBus` per workspace (`RunRegistry` on `app.state.runs`), recovers each, logs and skips unreadable databases, and closes them on shutdown. `list_workspaces` added to `services/projects/`.
- CLI: `spool runs list <project> [--ticket] [--limit]` and `spool runs show <project> <run_id>` (new `cli/runs.py`), read-only and without the daemon. The table helper moved to `cli/common.py`.
- Docs: `docs/runs.md`, "Runs" in `docs/architecture.md`, README commands, DECISIONS 59–70.
- Tests: schema and migrations, append-only triggers, numbering across runs, lifecycle, usage sums, payload limits, files and path escapes, bus order/filter/lag/resync/isolation and 4 × 250 concurrent appends, persist-before-publish, recovery scope, a killed subprocess recovered by a new instance (integration), lifespan with a stale run and a corrupt database, the lock (in-process and against `spool serve`), and the CLI.

## T08 · Git workspace manager

- `services/git/runner.py`: `run_git(args, cwd, timeout=60)` as an argument list with `-c core.quotepath=off -c core.fsmonitor=false`, a non-prompting C-locale environment (`GIT_TERMINAL_PROMPT=0`, `GIT_OPTIONAL_LOCKS=0`, repository-location variables removed, empty stdin), `git` resolved once with `shutil.which`; `GitError` with the command, exit code and last 20 stderr lines (`git worktree add failed (exit 128): fatal: …`); `check_git_version()` (2.36 minimum).
- `naming.py`: `slugify` (NFKD, ASCII, lowercase, `-` runs, 40-character cut, `ticket` fallback) and `branch_name` → `feat/<id>-<slug>`, the id checked against the ticket id pattern (moved to `core/ids.py`) and the name against `git check-ref-format --branch`.
- `repo.py` (now on `run_git`): `ensure_clean` (tracked, staged and untracked changes, 20 listed then `… and N more`), `ensure_no_operation_in_progress` (rebase, merge, cherry-pick, revert), `default_branch_sha`.
- `worktrees.py`: `WorktreeManager(repo, project, default_branch, root)` with `create` (checks, stale marked branch recreated, unmarked branch refused, rollback after a failed `worktree add` or marker), `resume`, `commit_all` (`--no-verify`, `user.useConfigOnly`), `teardown` (`worktree remove --force`, read-only-safe `rmtree` fallback, prune, marked branch only, idempotent), `session` with `keep()`, and `list_worktrees` from `git worktree list --porcelain -z` plus unknown folders, with states `ok`, `missing folder`, `not registered`, `no marker`.
- `recovery.py`: `recover_worktrees(manager, keep)` prunes, removes registered and orphan worktrees under the project's root that aren't kept, reports every entry (`pruned`, `removed`, `removed_orphan`, `kept`, `failed`) with path and reason and logs one line each.
- Daemon: the lifespan checks git's version (logs and keeps serving if too old), then recovers worktrees for every workspace after run recovery, keeping tickets whose latest run is `blocked` or `awaiting_approval` (`api/worktrees.py`); a missing repo or failing git is logged and skipped. New `worktrees_dir` setting.
- CLI: `spool worktrees list <project>` (new `cli/worktrees.py`), read-only.
- import-linter: `services.git` may not import any other service package.
- Docs: `docs/git.md`, "Git" in `docs/architecture.md`, README status and commands, a docs index, DECISIONS 71–83.
- Tests: exact slugs and `check-ref-format`, injection titles create no files, quotes and `;` in a title, create/dirty/in-progress/missing branch/stale and unmarked branches/second create/rollback, resume, commit (parent, no-op, failing `pre-commit` hook, verbatim message, missing identity), teardown (idempotent, keep branch, unmarked branch, read-only files with and without git's help), session (exception, keep), listing states, recovery of the six cases and a second pass, a killed subprocess recovered (integration), lifespan with a stale and a blocked worktree and a missing repo, old git at startup, runner errors, the CLI.

## T09 · Agent runner and Claude Code CLI

- `services/agents/model.py`: `AgentPolicy` (`for_worktree(worktree, commands, home)`: stack commands with shell operators, wildcards or surrounding spaces refused with `PolicyError` naming the field; read-only git; exact and prefix `Bash(...)` rules; the credential deny list plus the SpoolHQ home, or the token and everything beside the worktree's path when the worktree is inside the home), `Budget`, the events (`Started`, `Message`, `ToolCall`, `FileEdit`, `Usage`, `PermissionDenied`, `RateLimit`), `Outcome`, `RunResult`, `BackendInfo`.
- `runner.py`: the `AgentRunner` protocol and `BackendUnavailableError`.
- `claude_stream.py`: the pure `ClaudeStreamParser`: usage once per message id, `FileEdit` on a successful edit inside the worktree (warning for one outside), denials from `permission_denied` messages and the result's `permission_denials` (deduplicated, each logged as a warning), rate limits, the outcome mapping (usage limits from a rejected `rate_limit_event`, an assistant `rate_limit` error or `usage limit…|<epoch>` text), micro-USD cost for API billing only, unknown events counted in `debug`; `PolicyViolation` for unrequested tools, a wrong permission mode or a message before `init`.
- `claude_cli.py`: `ClaudeCliRunner` with `detect()` (`--version` and `auth status` with a 15 s timeout and the scrubbed environment, billing from `authMethod`, subscription before `ANTHROPIC_API_KEY`, 2.1.259 minimum, Windows refused with a WSL2 hint, Linux needs `bwrap` and `socat`), `build_argv` (the documented order, `Glob`/`Grep` included, `--max-budget-usd` for API billing only), `sandbox_settings`, `child_env` (allowlist plus `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` and `DISABLE_AUTOUPDATER=1`), and `run()`: prompt on stdin, reader threads, callbacks on the calling thread, token budget, timeout, cancel, SIGINT → SIGTERM → SIGKILL to the process group (terminate/kill on Windows), teardown that always kills the group and closes the pipes, last 50 stderr lines in errors. The worktree may not overlap the user's home or a denied path.
- `fake.py`: `FakeRunner(transcript)` replays through the same parser and performs `Write` calls inside the worktree. `backends.py`: `available_runners()`.
- CLI: `spool agents` (new `cli/agents.py`) shows each backend's install, version, login (method, billing) and whether the policy is enforceable, with install/login hints; always exits 0.
- import-linter: `services.agents` may not import any other service package. New pytest marker `real_agent`.
- Docs: `docs/agents.md`, "Agents" in `docs/architecture.md`, README, `docs/testing.md` (fake runner, fake `claude`, real run), DECISIONS 88–104.
- Tests: policy validation and rules; the exact argv, budget flag, no prompt or skip-permissions flags in argv; settings JSON; environment allowlist; parser outcomes, usage per message id, cost, file edits in and outside the worktree, denials and their warning, usage limits (event, assistant error, text with and without epoch), init violations, unknown events; the adapter end to end through `fake_claude.py` (argv and stdin, scrubbed environment, callback order and thread, API billing, denial, usage limit, policy violation, the `default` mode, token budget, timeout and cancel leaving no process behind, exit without result, old version, logged out, not installed, Windows/Linux/macOS rules); the fake runner (file written, cancel, budget, violation, replay of the real recording); a guard against `--dangerously-skip-permissions`/`bypassPermissions` in `services/agents/`; `spool agents`. Fixtures in `tests/fixtures/agents/claude/`, plus `recorded/real_run.jsonl` from the real run.
- Claude Code 2.1.302's env-scrub placeholders (`.env*`, `package.json`, lockfiles, `.claude/`, `node_modules/`) are removed from the worktree after a run when new and still empty, and `detect()` probes in a throwaway temp folder (DECISIONS 104).
- Real run (`-m real_agent`, `SPOOLHQ_REAL_AGENT=1`) passed against Claude Code 2.1.302 on Linux: `hello.txt` created, the `python3` call denied, tokens reported, the worktree left with only `.git` and `hello.txt`.
- The usage-limit fixture uses epoch `1792317600`, which is `2026-10-18T10:00:00Z` (the ticket's `1792310400` is 08:00Z).

## T10 · Context pack and prompts

- `services/context/`: frozen inputs (`TicketView`, `DependencyView`, `RepoDocs`, `GateFailure`, `ReviewNote`, `PreviousAttempt` with T07's retry kinds validated, `ContextInputs`) in `model.py`; `build_implementer_prompt(inputs, override_dir=None) -> RenderedPrompt` (`text`, `chars`, `cuts`, `template`) and the generic `render_template` in `render.py`; the default template `prompts/implementer.md.j2` as package data. Imports no other service package (new import-linter contract).
- The prompt: role, rules, commands (stack commands plus read-only git), on a retry a `<previous_attempt>` block (failing tests verbatim, gate output capped at 8,000 characters, review notes, conflicts, user note), the `<ticket>` block, then `<claude_md>`, `<spec>`, `<progress_log>`, `<decisions>`, and the `<progress>` reply contract. Jinja2 sandbox, untrusted text only as variables, closing tags escaped in Python, fences longer than any backtick run, LF only, no paths or dates.
- Budget (`budget.py`): characters, `context.max_chars` (new in `project.yaml`, 20,000–2,000,000, default 120,000); `CLAUDE.md` keeps its beginning (16,000), the spec its outline plus the most relevant sections, `PROGRESS.md` and `DECISIONS.md` their newest `## ` entries (24,000 each); cut notes in each block and in `cuts`; `ContextBudgetError` when the untrimmable parts leave under 2,000 characters.
- Overrides in `<workspace>/prompts/implementer.md.j2`, with one-line errors for undefined variables (with the line), syntax errors and sandbox violations.
- `progress.py`: `extract_progress_note` (last `<progress>` block, collapsed, at most 1,000 characters) and `format_progress_entry` (heading with the merge date, `<`, `>` and `#` lines removed). Nothing writes `PROGRESS.md` yet.
- CLI: `spool prompt show <project> <ticket>` (new `cli/prompt.py`) prints the initial prompt to stdout and `template: default · 2,662 of 120,000 characters` plus any cut notes to stderr.
- Dependency: `jinja2==3.1.6` (BSD-3-Clause). `.gitattributes` forces LF for `daemon/tests/fixtures/**` (the round-trip ticket fixtures keep `-text`).
- Docs: `docs/context.md`, "Context" in `docs/architecture.md`, `context.max_chars` in `docs/project-yaml.md`, the command in the README, DECISIONS 105–117.
- Tests in `tests/services/context/` and `tests/cli/test_prompt.py`: golden-file snapshots of the initial and gate-retry prompts (`tests/fixtures/context/expected/`, rewritten with `SPOOLHQ_UPDATE_SNAPSHOTS=1`), each retry kind, injection (template syntax, closing tags, fences), every budget rule, overrides and their errors, the progress note, `context.max_chars` validation, the CLI, package data in the built wheel, and a guard against `from_string`.
