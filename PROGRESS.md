# Progress

Newest entries at the bottom. One entry per merged ticket.

## What exists

Built: T01–T20, T27–T34. Older entries are in [docs/progress-archive.md](docs/progress-archive.md); code layout in [docs/architecture.md](docs/architecture.md).

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
- **Secrets** (`services/secrets/`): Anthropic, GitHub and ClickUp secrets in the OS keychain, write-only over the API; each can be tested with one read-only call to its provider.
- **API** (`api/`): REST for projects, tickets, spec, settings, runs, plan, agents, templates, secrets; one error format; ETags; WebSocket events with replay.
- **CLI** (`cli/`): `spool serve`, `init`, `project`, `tickets`, `plan`, `run`, `runs`, `review`, `gates`, `prompt`, `templates`, `agents`, `worktrees`, `github`, `secrets`.
- **Desktop** (`desktop/`): Tauri 2 + React, token kept in Rust, event bridge, Home with Needs you, New project, Settings (also from the panel), project panel with run controls and the Spec tab.
- **Not built yet**: tracker sync (T24; `services/tracker/` is empty), Tickets tab (T21), Run tab (T22), New project flow (T35), packaging (T23), dogfood (T25), release docs (T26).

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

## T34 · Settings polish and secret test

- Daemon: `POST /api/settings/secrets/{secret}/test` (`services/secrets/check.py`): reads the secret with the new `read_secret` (env, then keychain) and makes one read-only HTTPS `GET` to a fixed URL per provider (Anthropic `/v1/models`, GitHub `/user`, ClickUp `/api/v2/user`) with `httpx`, no redirects, 10 s; answers `{ok, message}` with fixed text only and logs one line with the name and outcome. TS client regenerated.
- Settings dialog: underlined tabs (Agents, Accounts, General, About), ✕ and a footer with **Done**, both disabled with the reason while no backend is ready on first run. Agents: the SDK without a key is grey ("Needs an API key (optional)"), amber only when nothing is ready, the raw daemon message under a collapsed "Details". Accounts: password field with Save, Test and Remove per secret, status as icon + label, the PNG's help lines, test result under the field ("Key works · tested just now" or the failure), kept only while the dialog is open.
- Panel: a gear at the right end of the breadcrumb row opens the same dialog, also with an invalid `project.yaml`. Run next / Run all and Generate plan / Retry are disabled with "Set up an agent first…" when no backend is ready, with an **Open Settings** link that opens the Agents tab (`openSettings`).
- ruff: `PLW1514` enabled (preview rule, explicit) and `scripts/` now linted; no findings, 0 files changed.
- Tests: daemon (each provider's 200, 401, 403, 500, timeout, network error, redirect not followed, not set makes no call, env value used, no token 401, unknown name 422, secret absent from every answer and log record), Vitest (tabs, ✕, Done, first run both ways, SDK neutral and Details collapsed, amber only when blocking, value gone after Save, Test disabled when not set, each result with its icon and gone after closing, gear with invalid settings, Open Settings opens Agents).
- Docs: `api.md` (testing a secret), `context.md` (split `DECISIONS.md`); DECISIONS 332–336.
