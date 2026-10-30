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
- refactor: `claude_cli.py` split into `claude_cli.py` + `claude_config.py`, `runs/log.py` into `log.py` + `rows.py`; `just lint` fails on a source file over 500 lines (`scripts/check_line_limit.py`, no exemptions) (DECISIONS 127).

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

## T11 · Quality gates

- `services/gates/` (new; imports no other service package, new import-linter contract): `GateStatus`, `GateResult`, `GateRun` (`passed`, `first_failure`, `to_gate_failures()` in T10's `GateFailure` shape) and `DoneWhenCheck` in `model.py`; `split_command` / `check_gate_command` (shell syntax refused), `resolve_program` and `gate_env` in `command.py`; `run_process` in `process.py` (new session, stdin closed, merged output streamed to a 20 MB-capped log, SIGTERM → SIGKILL to the group or `taskkill /T /F` on timeout); the pure output rules in `output.py`; `run_gates` and `check_done_when` in `runner.py`.
- The environment allowlist moved from `services/agents/claude_config.py` to `core/agent_policy.py` (`allowed_env`); `child_env` uses it, unchanged in behaviour.
- `project.yaml`: shell syntax and unclosed quotes in `commands.*` are validation errors; new optional `gates.timeouts` (10–7,200 s; 600/300/900 by default).
- CLI: `spool gates run <project> [--path <dir>]` (new `cli/gates.py`): prints the temporary log folder, one line per gate, each failing gate's excerpt and the failing tests; exits 1 unless all pass.
- Docs: `docs/gates.md`, "Gates" in `docs/architecture.md`, `gates.timeouts` and the shell rule in `docs/project-yaml.md`, the command in the README, the docs index, `docs/testing.md`, DECISIONS 128–138.
- Tests in `tests/services/gates/` (with `fake_tool.py`: `pass`, `fail-test`, `lint-error`, `sleep`, `sleep-with-child`, `flood`, `print-env`, `ansi`, plus `marker` for the never-run check) and `tests/cli/test_gates.py`: failing test, lint error and timeout results; 50,002 lines trimmed with the first failure kept and the full log intact; order and skips; the process tree gone after a timeout (POSIX via the child's pid, Windows via `tasklist`); secrets absent and `CI`/`NO_COLOR` present; shell syntax, quoted arguments and a missing program; ANSI, CRLF and invalid UTF-8; first-failure priority; Vitest names; the cap; "Done when" mapping with an unconfigured command never run; determinism; `gates.timeouts` validation and defaults; the CLI.
- The ticket's flood numbers didn't add up (20,000 + 1 + 29,000 + 1 is 49,002 lines, not 50,002); `fake_tool.py flood` prints a header, 20,000 passing lines, the first failure, 29,998 passing lines, the second failure and `2 failed, 49998 passed`, which is 50,002 lines and matches its own summary.

## T12 · Reviewer agent

- `services/agents/`: `AgentPolicy.read_only` and `read_only_for(worktree, home)`; for it the adapter passes `--tools Read,Glob,Grep` and `--allowedTools Read Glob Grep` (no Bash rules, Edit or Write) and `init` must list exactly those tools (`ClaudeStreamParser(exact_tools=…)`, `claude_config.requested_tools`). Writing policies are unchanged. `FakeRunner` takes a sequence of transcripts (one per run, raising past the end) and records `calls`.
- `services/review/` (new; may import only `services.agents` and `services.context`, new import-linter contract, and added to the other service contracts): `ReviewInputs` (no transcript, summary or progress field), `ItemVerdict`, `ReviewResult` with `unmet()` in `model.py`; `parse_verdict` / `InvalidVerdict` in `verdict.py` (strict Pydantic schema, index and consistency checks, gate answers merged before consistency); `trim_diff` (150,000 characters) in `diff.py`; `review()` in `reviewer.py` (read-only policy, one retry with the errors, `needs_human` after two invalid answers, outcomes other than `completed` passed through, usage summed). Prompt: `services/context/prompts/reviewer.md.j2`, overridable in `<workspace>/prompts/`.
- CLI: `spool review <project> <ticket> [--path] [--base]` (new `cli/review.py`): clean work tree required, diff `<base>...HEAD`, prints ✓/✗ per item, the verdict and summary; exits 0/1/2.
- Docs: `docs/review.md`, read-only policies and the fake runner's sequences in `docs/agents.md`, "Review" in `docs/architecture.md`, README, docs index, `docs/testing.md`, DECISIONS 139–153.
- Tests in `tests/services/review/`, `tests/cli/test_review.py`, `tests/services/tickets/test_checklist.py` and new cases in `tests/services/agents/`: the three verdicts, invalid then valid, invalid twice, gate override and re-validation, prompt contents, closing-tag injection, outcomes (usage limit, timeout, cancel, error, max turns, budget), diff trimming over 12 files, the parser's error cases, read-only argv and init checks (parser, fake, the adapter through `fake_claude.py`), fresh inputs, the CLI. Fixtures in `tests/fixtures/review/`, including `recorded/real_review.jsonl`.
- Real review (`-m real_agent`, Claude Code 2.1.302, Linux), three runs on the seeded diff: `changes_requested` each time, item 2 (`A test covers parse_slug`) not met, items 1 and 3 present (item 3 not met: no justfile in the scratch repo); one attempt each.

## T13 · Run loop

- `services/runloop/` (new; the one service that imports the others, new import-linter contract that no service imports it): `machine.py` (pick → implement → commit → gates → review → integrate over a `RunContext`; retry counters and the retry prompt's previous attempt read from the attempt rows and files; budget check; agent outcomes), `loop.py` (`RunLoop`: start `next`/`all`, pause, resume after a pause, a usage limit or a crash, cancel, discard, current; one worker thread per active run), `integrator.py` (`Integrator`, `IntegrationResult`, `HoldForIntegration`), `lock.py` (`.spoolhq/run.lock`), `resume.py` (`ResumeTimer`, reset + 60 s, clock-driven), `model.py`.
- `services/runs/`: schema version 2 (`runs.progress_note`, `runs.reset_at`), `set_run_status(…, reset_at=)`, `reopen_run`, `set_progress_note`, event kind `run.phase`, `RunRegistry.open`; `Transaction` moved to `rows.py` to keep `log.py` under 500 lines.
- `core/daemon_lock.py`: `acquire_lock(path)` / `LockHeld`, shared by the daemon lock and the run lock.
- `services/agents/`: `permission_modes(env, argv)`: init mode `default` only with `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` in the child environment and `--permission-prompts none`.
- API: `api/routers/runs.py` and `api/schemas/runs.py` (start, pause, resume, cancel, discard, current; token required; 404/409 with `detail`); the lifespan builds the `RunLoop` with the installed Claude Code for both roles and closes it on shutdown. CLI: `spool run next|all|pause|resume|cancel|discard|status` (`cli/run.py`), following a run once a second; `ApiClient.post`, error `detail` shown.
- Docs: new `docs/run-loop.md`; `docs/runs.md` (schema 2, `run.phase`, `reopen_run`), `docs/architecture.md`, `docs/agents.md`, `docs/testing.md`, the other service pages' T13 references, README commands, `CLAUDE.md`'s service list, DECISIONS 154–176.
- Tests: `tests/services/runloop/` (happy path with the phase order and the commit on the run branch, gate retry and review retry prompts, every blocked path, cancel, pause and resume, usage-limit pause and automatic resume without using a retry, reviewer usage limit, crash resume and discard, missing worktree, the lock after done, blocked, cancel and an exception, budget, reviewer changing the worktree, hold for integration, `run all` in order and stopping at a blocked ticket, refusals, the resume timer), `tests/api/test_runs.py`, `tests/cli/test_run.py`, run log schema 2 and the permission-mode check.
- Real run (`-m real_agent`, Claude Code, Linux): the scratch ticket (`hello.py` + test) went `done` in 1 attempt (`initial` → approved), 47,383 input and 1,627 output tokens; the reviewer approved. The commit included `__pycache__/*.pyc`, because the scratch repository has no `.gitignore` and `commit_all` stages everything.

## T14 · Local integration

- `services/git/integrate.py` (new): `merge_in` (`--no-ff --no-commit`, conflicts left in the worktree), `conflict_files`, `unresolved_files` (unmerged entries and marker lines), `conclude_merge` and `commit` (identity required, hooks off), `start_squash` (detached `HEAD`, soft reset onto main), `unstage`, `stage`, `restore_branch`, `ensure_main_ready`, `advance` (`merge --ff-only` or `update-ref` compare-and-swap), `create_tag`, `tag_exists`, `is_ancestor`, the diff guard (`is_junk`, `is_secret`, `too_large`) and `commit_message`.
- `services/runs/`: schema version 3 with the `integrations` journal; `journal.py` with `start_integration`, `set_integration_state` and `open_integrations`; event kind `integrate`.
- `services/runloop/integration.py` (new): `LocalIntegrator`, which merges main in, reruns the gates when that brought anything, squashes with the `PROGRESS.md` entry, advances main (3 tries), tags and finishes, writing a journal state before each step and taking a test-only `checkpoint` callback. Also `finish`, shared with recovery, and `recover_integrations`. `machine.py`: conflicts start one `conflict_retry`, whose markers are checked before its commit concludes the merge; `gates_failed` after the merge starts a `gate_retry`; integration can be the first step of `drive`. `loop.py`: `LocalIntegrator` by default, `HoldForIntegration` for `run.integration: hold`, `integrate_ticket`, and `resume`'s second half shared as `_continue`. `user_errors` moved to `model.py` to keep `loop.py` under 500 lines.
- `services/context/`: `PreviousAttempt.system_note`, rendered as "Note from SpoolHQ" ahead of "Note from the user".
- `services/projects/`: `run.integration: local | hold`.
- API: `POST /api/projects/{name}/tickets/{id}/integrate`; startup runs `recover_all_integrations` before worktree recovery (`app.state.integration_recovery`). CLI: `spool run integrate <project> <ticket>`.
- Docs: new `docs/integration.md`; `docs/run-loop.md`, `docs/git.md`, `docs/context.md`, `docs/runs.md` (schema 3, `integrate`), `docs/project-yaml.md`, `docs/architecture.md`, `docs/testing.md`, the docs index and the README; DECISIONS 177–194.
- Tests: `tests/services/git/test_integrate.py` (message, guard lists, merge-in, markers, squash shape, both advance modes, moved main, dirty checkout, tags), `tests/services/runs/test_journal.py`, `tests/services/runloop/test_integration.py` (three tickets give three tagged squash commits with green gates rerun at each, plus PROGRESS entries; main moved before integration, and moving during the advance once and three times; gates failing after the merge; conflict resolved, markers left, a second conflict; dirty checkout then `integrate_ticket`; junk left out and listed, `.env`, `.env.example`, a 6 MB file; an existing tag; hold mode; a git error mid-squash), `tests/services/runloop/test_integration_crash.py` with `crash_child.py` (`os._exit(1)` after each journal state, then recovery twice; a dirty checkout and a mid-merge main checkout during recovery), the notes split in `tests/services/context/test_render.py`, `run.integration` validation, the API endpoint and `spool run integrate`.

## Chore · M1 findings

- The implementer no longer gets `install` (`Commands.for_implementer()`); the diff guard drops `.pnpm-store/`, `.npm/` and `.yarn/cache/` and blocks symlinks pointing outside the repo; the reviewer ignores sandbox placeholder files (with a new prompt snapshot); `.gitignore` ignores `.pnpm-store/`; DECISIONS 195–199.

## T29 · Show the commit and tag in spool run status after a merge (2026-10-24)

T29 made `spool run status` show `last merged: ticket · short sha · ticket/id` under `no active run in 'project'`. The data comes from the newest finished row in the integration journal (`last_integration` → `last_merged` → `Current.last_merged`), and `runs/current` returns it as `last_merged`. A CLI test after a real merge covers it.

## Chore · Cut tokens per ticket

- The token budget counts weighted tokens (cache reads at a tenth), with `cache_read_tokens` stored per attempt (schema 4) and the weighted total in `spool runs list|show`; the implementer prompt asks for fewer, larger turns; the prompt keeps the newest 3 `PROGRESS.md` entries and 20 `DECISIONS.md` lines (`context.progress_entries`, `context.decisions_lines`); the implementer's env sets `npm_config_verify_deps_before_run=false`; DECISIONS 202–205.
- Real run (the T13 hello ticket): 1 attempt, 6 model calls, 60,551 in (49,447 cache reads) and 1,848 out, 17,896 weighted. Before (T13): 47,383 in and 1,627 out, cache reads and calls not recorded.

## T15 · Planner agent

- `services/planner/` (new): the `<plan>` schema and title cleaning (`model.py`), parsing and checks against the kept tickets and T06's graph validation (`validate.py`), the sandboxed prompt (`prompt.py`, template `services/context/prompts/planner.md.j2`), draft files, `plan.json` hashes, the re-plan split, all-or-nothing writes and `approve_plan` (`store.py`), and `generate_plan` with one retry and the token budget (`planner.py`).
- Run log: `runs.kind` (`ticket` | `plan`, schema 5), `start_plan_run`, attempt kind `plan` in `runs/plan/`; resume skips plan runs. `services/runloop/planning.py`: `PlanJobs` runs the planner on a daemon thread; `Agents.planner`.
- CLI: `spool plan generate|show|approve`. API: `POST /api/projects/{name}/plan` (202) and `/plan/approve`; `RunView.kind`.
- `slugify` moved to `core/ids.py`. Fixtures: the dashboard spec and a recorded 18-ticket plan run (`tests/fixtures/planner/`), the golden planner prompt.
- Docs: new `docs/planner.md`; `ticket-format.md`, `agents.md`, `project-yaml.md`, `runs.md`, `architecture.md`, `context.md`, `scheduler.md`, `testing.md`, the docs index and the README; DECISIONS 206–220.
- Real run (a three-paragraph spec for a small CLI tool): 1 call, 19,138 in (15,506 cache reads) and 3,414 out, 8,596 weighted; six tickets, valid.

## T16 · Template library

- `services/templates/` (new): the `spoolhq-template.yaml` contract (`contract.py`), built-in names, local folders and git URLs resolved to a commit (`sources.py`), Copier without trust plus `git init` and the first commit, with clean-up on failure (`generate.py`), and the contract check through T11's gates (`check.py`). Copier 9.19.1 (MIT) is the one new dependency.
- `spool init --template SOURCE [--template-ref REF]` generates into a new or empty `--repo`, commits `chore: apply template <name>` and fills `project.yaml`'s `commands` and new `template` block (`name`, `source`, `ref`); the description goes to the workspace's `TEMPLATE.md`, which `spool plan generate` (and the API) use when no description is given. `spool templates list|check`.
- The built-in `fastapi-react` template (`daemon/src/spoolhq/templates/fastapi-react/`): FastAPI, SQLAlchemy 2, Alembic, pytest (80% floor), ruff, mypy strict and import-linter layers in `backend/`; React, Vite, strict TypeScript, Vitest, ESLint, Prettier and Feature-Sliced Design enforced by eslint-plugin-boundaries in `frontend/`; an `items` example through every layer, a justfile, CI, `CLAUDE.md`, `PROGRESS.md`, `DECISIONS.md`, `.gitignore` and `.env.example`. It passes its own gates with no agent (about 10 s locally with warm caches).
- Docs: new `docs/templates.md`; `project-yaml.md`, `planner.md`, `architecture.md`, `testing.md`, the docs index, the README and `templates/README.md`; DECISIONS 221–231.

## T17 · GitHub delivery

- Step 0: git-URL templates are checked out through `run_git` (hooks and signing off) and given to Copier as a plain folder, so Copier never runs git; the answers file keeps the URL and commit. The `fastapi-react` template uses `httpx` again: `httpx2` is Pydantic's continuation, not one the HTTPX maintainers named (DECISIONS 233–234).
- `services/git/remote.py`: fetch into `refs/spoolhq/remote/<branch>`, unpushed commits, plain pushes (`moved` vs. other refusals with git's error), tags, remote branch deletion, `owner/repo` from the URL.
- `services/github/` (new): `GitHubClient` (token, API headers, 30 s timeouts, rate limits, redaction), pull requests, reviews and review comments, and the token (`SPOOLHQ_GITHUB_TOKEN`, else the OS keychain via `keyring` 25.7.0, MIT).
- `services/runloop/delivery.py`: `delivery_mode` and `Delivery` (the run loop's default integrator): fetch first, push before advancing local main, at most 3 redos when main moves; PR mode pushes `spoolhq/<id>-<slug>`, opens the PR (`pr_body.py`: escaped, capped at 60,000 characters) and waits. `polling.py`: `GitHubPoller` (every 60 s and `spool github sync`) finishes merged PRs, starts `pr_changes` attempts for requested changes and blocks closed ones. Journal states `pushed` and `pr_open`; recovery asks the remote. Run log schema 6: the run's PR number, URL and branch.
- CLI `spool secrets set github`, `spool github sync`; the PR in `spool run status`, `spool tickets show` and the run views; `POST /api/projects/{name}/github/sync`.
- Docs: new `docs/github.md`; `integration.md`, `git.md`, `project-yaml.md`, `run-loop.md`, `runs.md`, `context.md`, `templates.md`, `architecture.md`, the docs index and the README; DECISIONS 233–245.
- Tests use a local bare repository as the remote (`url.<bare>.insteadOf`) and a fake GitHub API (`httpx.MockTransport`); the opt-in test against a real repository (`SPOOLHQ_GITHUB_TEST_REPO`) was not run.

## T18 · Merge policy

- Step 0: a local template folder that is a git repository is cloned through `run_git` (hooks and signing off) at `--template-ref` (default `HEAD`) and handed to Copier as a plain folder; remote git calls run ssh with `BatchMode=yes` unless the user set their own ssh command (kept, one warning). DECISIONS 246–247.
- `services/runloop/policy.py` (new, pure): the rules (`needs_human`, `review_required`, `diff_size`, `protected_paths`, `hold_mode`), the path matcher, `PolicyDecision`, `delivery_mode` and `describe`. `services/git/diffstat.py` (new): the staged squash's files and line counts, renames included.
- `services/runloop/approval.py` (new): the decision on the staged squash during integration (event `policy.decision`, run row `policy`, schema 7), local approval, `approve` and `reject`. A `needs_human` verdict with passed gates now goes to a person; hold mode is the `hold_mode` rule. PR bodies start with "Why this needs you".
- `project.yaml`: `merge_policy.max_diff_lines` (10–100,000), `protected_paths` (replaces the new default list), `protected_paths_extra`; bad patterns are refused by field.
- CLI `spool run approve` (alias `integrate`), `spool run reject --note`; the decision in `spool run status` and `spool runs show`. API `POST /api/projects/{name}/tickets/{id}/approve` (alias `/integrate`) and `/reject`; `policy` on the run view.
- Docs: new `docs/merge-policy.md`; `github.md`, `run-loop.md`, `review.md`, `project-yaml.md`, `integration.md`, `runs.md`, `architecture.md`, `templates.md`, the docs index and the README; DECISIONS 246–256.

## T27 · Agent roles, custom endpoints and contract suite

- `services/agents/backends.py`: a registry from backend name to factory `factory(base_url, model)`; only `claude-code-cli` is built in, and tests register fakes. `ClaudeCliRunner(base_url=…, model=…)` passes `ANTHROPIC_BASE_URL` in that child's environment and `--model` on its command line; without them, argv and environment are unchanged.
- `project.yaml`: `agents.default`, `planner`, `implementer` and `reviewer` are checked against the registry (so `codex-cli`, `gemini-cli` and `claude-agent-sdk` are refused until T30/T31). New `agents.backends.<name>.base_url` (http(s); plain http only to localhost; no credentials) and `.model`.
- The daemon builds each role's runner per project (`Agents.for_project`; `PlanJobs` for the planner); `spool plan generate` and `spool review` use the project's roles. `spool agents --project <name>` shows each role's backend, model and endpoint.
- `tests/services/agents/test_contract.py`: one suite over adapter cases (Claude Code through the fake binary, and `FakeRunner`, which gained `name` and `stall_s`): file created, denial logged, usage-limit pause, timeout, cancel, weighted usage.
- Docs: `agents.md` (roles and backends, local models with Ollama, contract suite), `project-yaml.md`, `planner.md`; DECISIONS 257–260. The opt-in real run passes with every role set explicitly.

## T30 · Codex CLI backend

- Step 0: with a custom `base_url`, SpoolHQ supplies the endpoint's credential (`services/agents/endpoint.py`): a dummy for localhost, else `SPOOLHQ_ENDPOINT_TOKEN_<BACKEND>` or the keychain (`spool secrets set endpoint:<backend>`); a remote endpoint without one is refused. Claude Code gets it as `ANTHROPIC_AUTH_TOKEN`, which outranks the claude.ai login, and never `ANTHROPIC_API_KEY`.
- `services/agents/codex_cli.py`, `codex_config.py`, `codex_stream.py` (new): `codex exec --json` under a per-run permission profile (`:workspace` for the implementer, worktree-only reads for the reviewer and planner, credential paths denied, no network), `approval_policy="never"`, `--ignore-user-config`, web search, apps, plugins, hooks and multi-agent off; registered as `codex-cli`. A policy part Codex can't enforce here is refused per role before starting. `process.py` (new) holds the process session both CLI adapters share.
- `AgentPolicy.role`; `BackendInfo.policy_parts`; `spool agents` shows Codex's parts per role and `codex login`.
- Tests: Codex in the contract suite, a run-loop ticket end to end on Codex, argv/profile/environment/refusal/stream tests, the opt-in real run (`SPOOLHQ_REAL_BACKENDS=codex`, not run: Codex isn't installed here).
- Docs: `agents.md` (custom endpoints, the Codex CLI section), `project-yaml.md`, `architecture.md`; DECISIONS 261–272.
