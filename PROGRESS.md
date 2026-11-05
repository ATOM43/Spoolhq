# Progress

Newest entries at the bottom. One entry per merged ticket.

## What exists

Built: T01–T20, T27–T33. Older entries are in [docs/progress-archive.md](docs/progress-archive.md); code layout in [docs/architecture.md](docs/architecture.md).

- **Tooling and CI**: monorepo (`daemon/`, `desktop/`, `templates/`, `docs/`), `justfile` (`install`, `lint`, `test`, `dev`), CI on Linux, macOS and Windows; ruff, mypy strict, import-linter, ESLint boundaries, 500-line limit, 85% daemon coverage.
- **Core** (`core/`): config from `config.toml` and `SPOOLHQ_*`, bearer token, JSON logs, single-instance lock, ticket ids and `slugify`, the agent environment allowlist.
- **Projects** (`services/projects/`): workspaces under `~/spoolhq-projects/`, `spool init`, `project.yaml` validated by Pydantic, invalid settings reported per project.
- **Tickets** (`services/tickets/`): Markdown tickets with frontmatter, byte-exact round trip, `spool tickets`, "Done when" parsing.
- **Scheduler** (`services/scheduler/`): dependency graph, status transitions, `next_ready`, cycles, critical path, `spool plan check`.
- **Run log** (`services/runs/`): SQLite per workspace (schema 7), append-only events, event bus, crash recovery, integration journal, usage totals.
- **Git** (`services/git/`): one worktree per run, owned branches, no hooks or signing, squash and fast-forward integration helpers, diff stats.
- **Agents** (`services/agents/`): `claude-code-cli`, `codex-cli` and `claude-agent-sdk` backends behind `AgentRunner`, role registry, custom endpoints, sandbox policy, `FakeRunner`, contract suite.
- **Context pack** (`services/context/`): sandboxed Jinja2 prompts for implementer, reviewer and planner, character budget, progress notes.
- **Gates** (`services/gates/`): install → lint → test without a shell, scrubbed environment, timeouts, failure excerpts.
- **Review** (`services/review/`): read-only reviewer with a fresh context and a strict JSON verdict.
- **Run loop** (`services/runloop/`): implement → commit → gates → review → integrate, retries, pause on usage limits, cancel, recovery, merge policy, approve and reject, GitHub PR polling.
- **Planner** (`services/planner/`): read-only planner writing draft tickets, `plan.json` hashes, `spool plan generate|show|approve`.
- **Templates** (`services/templates/`, `templates/`): Copier with no trust, `spoolhq-template.yaml` contract, built-in `fastapi-react`.
- **GitHub** (`services/github/`): direct push or pull requests per project and ticket, token from env or keychain.
- **Code graph** (`services/codegraph/`): optional offline Graphify map in implementer and planner prompts; this repo commits its own graph in `graphify-out/`.
- **Secrets** (`services/secrets/`): Anthropic, GitHub and ClickUp secrets in the OS keychain, write-only over the API.
- **API** (`api/`): REST for projects, tickets, spec, settings, runs, plan, agents, templates, secrets; one error format; ETags; WebSocket events with replay.
- **CLI** (`cli/`): `spool serve`, `init`, `project`, `tickets`, `plan`, `run`, `runs`, `review`, `gates`, `prompt`, `templates`, `agents`, `worktrees`, `github`, `secrets`.
- **Desktop** (`desktop/`): Tauri 2 + React, token kept in Rust, event bridge, Home with Needs you, New project, Settings, project panel with run controls and the Spec tab.
- **Not built yet**: tracker sync (T24; `services/tracker/` is empty), Tickets tab (T21), Run tab (T22), Settings polish (T34), New project flow (T35), packaging (T23), dogfood (T25), release docs (T26).

## T19 · Live API

- Step 0: route inventory in DECISIONS 295. Run control moved to `POST …/run/next|all|ticket/{id}|pause|resume|cancel` and plan generation to `…/plan/generate`; `spool run` uses them (`--run` becomes `?run_id=`).
- REST (`api/routers/projects.py`, `tickets.py`, `runs.py`, `agents.py`, `settings.py`): projects (list with progress, run state and needs-you count; create like `spool init`), `project.yaml` and `CONTEXT.md` with ETag + If-Match (428, 412 with the current ETag and content), tickets (filters, edits through the ticket store and the transition table, unblock with a note), paged run history (opaque cursor, stable under inserts), one run with its attempts, attempt files by enum (symlinks out are 404), agents, daemon settings and write-only secrets in the OS keychain. One error format everywhere; path patterns for names and ids; 1 MB body cap.
- WebSocket `…/events?since=`: auth as the first message (4401), origin check, envelope with `seq`, replay from SQLite after subscribing (no gaps, no duplicates), per-client queue of 1,000 filled only through `call_soon_threadsafe` (4408 when full; the run never waits), 20 s ping, 1001 on shutdown.
- Unblock reopens the blocked run in its kept worktree with a `pr_changes` attempt whose prompt has the note.
- TypeScript: `just gen-api` (schema dumped without a server, `openapi-typescript`), an `openapi-fetch` client through a new Rust command `daemon_request`, a WebSocket helper with `since` reconnects and backoff; drift checks for both generated files in `just lint`. New: `openapi-fetch` 0.17.0, `openapi-typescript` 7.13.0 (dev).
- Tests: every endpoint with the token and without (401), conflicting edits for tickets, spec and settings, round-trip of every T05 fixture, 120-run paging with an insert between pages, artifacts, secrets leak scan, a fake run's full event stream in order, replay from the middle and at the live seam, a client that never reads, auth and origin; Vitest for the 4408 reconnect and the 412 error.
- Docs: `api.md` (new), `architecture.md`, `run-loop.md`, `runs.md`, `planner.md`; DECISIONS 295–305.

## T20 · Event bridge, Home and New project

- Step 0: `Plan.md` splits T20 into T20 (this ticket, 2 h) and T32 (Settings, project panel and Spec tab, 2 h); T21 and T22 depend on T32. 31 tickets, 77 h, critical path 28.5 h.
- Events through Rust: `events_subscribe` / `events_unsubscribe` hold the daemon WebSocket (auth first, `since` reconnects with 0.5 s → 10 s backoff, final on 4401/4404/1008) and forward envelopes over a Tauri channel; `subscribeEvents` keeps its name on top of them, without `getToken()`. CSP unchanged. New: `tokio-tungstenite` 0.30.0.
- Query hooks in `entities/project`, `ticket`, `run`, `agent`; run events invalidate the project, ticket and run queries (coalesced, no polling).
- Home: project list with a progress line and status as icon + label, "Needs you" (blocked, awaiting approval, paused runs), empty, loading, error and daemon-missing states; recovers by itself when the daemon is back.
- New project dialog: name, repo (Tauri folder picker) or template from `GET /api/templates`; then the install, lint and test commands, each with **Test** (`POST …/commands/test`, gates code, no shell, 90 s), saved with the settings ETag. API field errors show next to their fields. New: `tauri-plugin-dialog` / `@tauri-apps/plugin-dialog` 2.8.3.
- Tests: Rust (auth first, `since` after 4408 and after a drop, unsubscribe closes with 1000, 4401 stops), Vitest (Home in every state, "Needs you" once per kind, a run event updates progress with one refetch, New project field errors, Test pass/fail/timeout, created project appears, daemon down → back), daemon (command test pass, fail, timeout, missing program, shell syntax refused and never run, cwd is the repo, no token → 401; template list).
- Docs: `architecture.md` (data and live events), `api.md`, `desktop/README.md`; DECISIONS 306–312.

## T32 · Settings, project panel and Spec tab

- Step 0: the frontend line limit already existed (`scripts/check_line_limit.py`, 500 lines, tests exempt, `schema.gen.ts` allowed) and was kept. Replay started from 0: the project and current-run answers now carry `latest_seq`, and `useProjectEvents` subscribes after it (DECISIONS 310, 313).
- Daemon: `ProjectDetail` gained `next_ticket`, `idle` and `remaining_h`; `CurrentRun` gained `cost_micro_usd`. `websockets` 17.2 added: `spool serve` could not serve the event WebSocket before (401), found in the real app run.
- Settings dialog (`features/settings`): Agents (version, login status and how to log in, Graphify), Accounts (write-only Anthropic, GitHub and ClickUp secrets, Set/Replace/Remove, value never kept), General (folders) and About; opens by itself on Home when no backend is ready and can't be closed until one is.
- Project panel (`pages/project`): header with repo copy, branch, remote, progress and usage; run controls for every state (Run next/Run all, Pause, Resume, Cancel through a confirm, usage-limit pause with its reset time), each disabled control with its reason; tabs Spec, Tickets, Run (the last two are placeholders until T21/T22), opening on the section-8 tab; loading, error, unknown-project and daemon-missing states.
- Spec tab (`widgets/spec-editor`): source / split / preview, autosave after 1 s and Ctrl/Cmd+S with If-Match, conflict bar with Reload and Keep mine, save state as icon + label, starter outline, Generate plan / Re-plan with reasons, progress and a failure bar with Retry.
- Untrusted text: `Markdown` (react-markdown 10.1.0, raw HTML skipped, unsafe URLs emptied); ESLint bans `dangerouslySetInnerHTML`.
- Tests: daemon (subscribe from `latest_seq` gets the event written in between and no history; readiness fields; WebSocket under real `spool serve`), Vitest (replay with a mocked bridge, Settings in every state and both first-run cases, the secret absent from the DOM and caches, run controls per state, autosave/412/Keep mine/Reload/Generate plan, inert markdown).
- Docs: `architecture.md`, `api.md`, `CLAUDE.md` layout; DECISIONS 313–322.

## T33 · Home and project panel polish

- Plan: T33, T34 and T35 added to Phase 4 (34 tickets, 83.5 h); T21 and T23 now depend on T35; critical path T01 → T02 → T04 → T05 → T06 → T13 → T19 → T20 → T32 → T33 → T34 → T35 → T21 → T23 → T26 (35 h).
- Daemon: the project list and detail report an invalid `project.yaml` per project (`settings_error` with file, field, message) instead of failing, plus `draft`, `remaining_h`, `has_spec`, `template`, `run`, `run_step`, `last_activity` and `usage` (tokens and USD summed from the run log, `services/runs/totals.py`). TS client regenerated.
- Home: full-width top bar (SpoolHQ, daemon status, Settings, + New project); Needs-you cards per kind with one action each (Unblock, Review, Review plan, Resume/Discard, Open run), hidden when empty; 320 px project cards with template badge, progress "13 of 18 done · 12 h left", status chip (icon + label, never "Unknown"), last activity and usage; daemon-down layout from the V1 PNG.
- Project panel: full width; breadcrumb, repo path with copy, branch, remote; guidance line by section-8 state or progress with usage; underlined tabs with counts; red invalid-settings bar with Reload; `?tab=` opens a tab; the Spec editor and preview fill the window and scroll on their own.
- Disabled controls: muted look and a CSS-only tooltip on hover and keyboard focus (`ReasonButton`).
- Spec toolbar: word count; Import .md (FileReader, confirm before replacing a non-empty spec).
- Tests: daemon (invalid `project.yaml` listed with its field while others load, usage sums, latest activity and step, `has_spec`, `split_error`), Vitest (every status label and icon, Settings invalid, each Needs-you kind and its action, hidden when empty, guidance per state, tooltip on hover and focus, invalid-settings bar and Reload, Import .md with and without confirmation).
- Docs: `api.md`; DECISIONS 323–329.

## Chore · Docs split

- `DECISIONS.md` is now an index (`NNN · title · area file`); the 329 entries moved word for word into `docs/decisions/<area>.md`: core, projects-tickets, runloop, agents, git-github, api, desktop, codegraph, tracker (empty).
- `PROGRESS.md` starts with a "What exists" summary and keeps the last 5 entries; older ones moved word for word to `docs/progress-archive.md`.
- `CLAUDE.md` holds rules only and says what to read first; the Graphify rebuild steps moved to `docs/codegraph.md`.
- `scripts/check_decisions.py` (in `just lint`): every index number has exactly one entry and the reverse, no gaps or duplicates, titles match the entry headings, each line names the right file. Tests in `daemon/tests/test_layout.py`.
- `task.md`'s example `merge_policy` already used the model's keys (`max_diff_lines`, `protected_paths`; fixed in 7b4f640), so it is unchanged.
- DECISIONS 330.

## Chore · Context pack reads split decisions

- `services/context/decisions.py`: `read_repo_docs(repo, count)` reads `CLAUDE.md`, `PROGRESS.md` and `DECISIONS.md`; a decisions index is expanded to the newest `count` full entries from their area files, in number order. The run loop and `spool prompt show` use it.
- Area paths from the index are read only inside the repo (no absolute, `..`, drive or symlink-out paths); a missing file or entry keeps its index line with one warning.
- A full `DECISIONS.md` renders byte-identical to before (checked against the existing snapshot).
- `task.md`: the example `project.yaml` has the `template` block and a valid `git.remote`; a test validates it against the model.
- DECISIONS 331.
