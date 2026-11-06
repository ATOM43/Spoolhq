# Progress

Newest entries at the bottom. One entry per merged ticket.

## What exists

Built: T01–T21, T27–T36. Older entries are in [docs/progress-archive.md](docs/progress-archive.md); code layout in [docs/architecture.md](docs/architecture.md).

- **Tooling and CI**: monorepo (`daemon/`, `desktop/`, `templates/`, `docs/`), `justfile` (`install`, `lint`, `test`, `dev`), CI on Linux, macOS and Windows; ruff, mypy strict, import-linter, ESLint boundaries, 500-line limit, 85% daemon coverage.
- **Core** (`core/`): config from `config.toml` and `SPOOLHQ_*`, bearer token, JSON logs, single-instance lock, ticket ids and `slugify`, the agent environment allowlist.
- **Projects** (`services/projects/`): workspaces under `~/spoolhq-projects/`, `project.yaml` validated by Pydantic (stack commands optional), invalid settings reported per project.
- **Creation** (`services/creation/`): a job that creates a project from a built-in template, an existing repo or an empty repo (workspace → repo → check commands → initial commit), refuses unsafe paths first and rolls back only what it created; `spool init` and `POST /api/projects` share it (only `spool init` takes folder or git URL templates, `--template-ref` and `--branch`); a project held by a running job is reported as `creating`, one whose rollback left paths as `cleanup_failed` (until dismissed).
- **Tickets** (`services/tickets/`): Markdown tickets with frontmatter, byte-exact round trip, `spool tickets`, "Done when" parsing.
- **Scheduler** (`services/scheduler/`): dependency graph, status transitions, `next_ready`, cycles, critical path, `spool plan check`.
- **Run log** (`services/runs/`): SQLite per workspace (schema 7), append-only events, event bus, crash recovery, integration journal, usage totals.
- **Git** (`services/git/`): one worktree per run, owned branches, no hooks or signing, squash and fast-forward integration helpers, diff stats.
- **Agents** (`services/agents/`): `claude-code-cli`, `codex-cli` and `claude-agent-sdk` backends behind `AgentRunner`, role registry, custom endpoints, sandbox policy, `FakeRunner`, contract suite.
- **Context pack** (`services/context/`): sandboxed Jinja2 prompts for implementer, reviewer and planner, character budget, progress notes.
- **Gates** (`services/gates/`): install → lint → test without a shell, scrubbed environment, timeouts, failure excerpts.
- **Review** (`services/review/`): read-only reviewer with a fresh context and a strict JSON verdict.
- **Run loop** (`services/runloop/`): implement → commit → gates → review → integrate, retries, pause on usage limits, cancel, recovery, merge policy, approve and reject, GitHub PR polling.
- **Planner** (`services/planner/`): read-only planner writing draft tickets, `plan.json` hashes, `spool plan generate|show|approve`, the plan summary and its problems (approve refuses while any exist).
- **Templates** (`services/templates/`, `templates/`): Copier with no trust, `spoolhq-template.yaml` contract, built-in `fastapi-react`.
- **GitHub** (`services/github/`): direct push or pull requests per project and ticket, token from env or keychain.
- **Code graph** (`services/codegraph/`): optional offline Graphify map in implementer and planner prompts; this repo commits its own graph in `graphify-out/`.
- **Secrets** (`services/secrets/`): Anthropic, GitHub and ClickUp secrets in the OS keychain, write-only over the API; each can be tested with one read-only call to its provider.
- **API** (`api/`): REST for projects, creation jobs, tickets, spec, settings, runs, plan, agents, templates, secrets; one error format; ETags; WebSocket events with replay.
- **CLI** (`cli/`): `spool serve`, `init`, `project`, `tickets`, `plan`, `run`, `runs`, `review`, `gates`, `prompt`, `templates`, `agents`, `worktrees`, `github`, `secrets`.
- **Desktop** (`desktop/`): Tauri 2 + React, token kept in Rust, event bridge, Home with Needs you, the New project dialog (three sources, live checklist, Fix), Settings (also from the panel), project panel with run controls, the Spec tab, and the Tickets tab with plan review and a read-only ticket drawer.
- **Not built yet**: tracker sync (T24; `services/tracker/` is empty), ticket editing and actions (T37), Run tab (T22), packaging (T23), dogfood (T25), release docs (T26).

## T34 · Settings polish and secret test

- Daemon: `POST /api/settings/secrets/{secret}/test` (`services/secrets/check.py`): reads the secret with the new `read_secret` (env, then keychain) and makes one read-only HTTPS `GET` to a fixed URL per provider (Anthropic `/v1/models`, GitHub `/user`, ClickUp `/api/v2/user`) with `httpx`, no redirects, 10 s; answers `{ok, message}` with fixed text only and logs one line with the name and outcome. TS client regenerated.
- Settings dialog: underlined tabs (Agents, Accounts, General, About), ✕ and a footer with **Done**, both disabled with the reason while no backend is ready on first run. Agents: the SDK without a key is grey ("Needs an API key (optional)"), amber only when nothing is ready, the raw daemon message under a collapsed "Details". Accounts: password field with Save, Test and Remove per secret, status as icon + label, the PNG's help lines, test result under the field ("Key works · tested just now" or the failure), kept only while the dialog is open.
- Panel: a gear at the right end of the breadcrumb row opens the same dialog, also with an invalid `project.yaml`. Run next / Run all and Generate plan / Retry are disabled with "Set up an agent first…" when no backend is ready, with an **Open Settings** link that opens the Agents tab (`openSettings`).
- ruff: `PLW1514` enabled (preview rule, explicit) and `scripts/` now linted; no findings, 0 files changed.
- Tests: daemon (each provider's 200, 401, 403, 500, timeout, network error, redirect not followed, not set makes no call, env value used, no token 401, unknown name 422, secret absent from every answer and log record), Vitest (tabs, ✕, Done, first run both ways, SDK neutral and Details collapsed, amber only when blocking, value gone after Save, Test disabled when not set, each result with its icon and gone after closing, gear with invalid settings, Open Settings opens Agents).
- Docs: `api.md` (testing a secret), `context.md` (split `DECISIONS.md`); DECISIONS 332–336.

## T35 · Project creation job

- Plan: T35 split into T35 (this, 2 h) and T36 · New project dialog (2 h); T21 and T23 depend on T36; 35 tickets, 84.5 h; critical path T01 → T02 → T04 → T05 → T06 → T13 → T19 → T20 → T32 → T33 → T34 → T35 → T36 → T21 → T23 → T26 (36 h).
- `services/creation/`: request model and checks (name `^[a-z][a-z0-9-]{0,39}$`, built-in templates only, untrusted path refused if root, home, inside SpoolHQ's folders or a symlink; existing repo clean; duplicate name), four steps with state, duration, fixed message, trimmed output and the request field, rollback of recorded paths newest first without following symlinks, in-memory jobs kept 1 h.
- API: `POST /api/projects` → 202 `{"job_id"}` or 422 with the field; `GET /api/jobs/{id}`, `POST /api/jobs/{id}/cancel`; `GET /api/templates` adds `summary`; the project detail reports `idle.code = "no_commands"`. TS client regenerated.
- `spool init` runs the same job in the foreground (`--source`, `--install/--lint/--test`, `--merge-preset`, `--clickup-list`); `--branch`, `--template-ref` and folder/URL templates are gone from it (`spool templates check` keeps them). `init_from_template` removed.
- Stack commands optional in `project.yaml`; without `test` the run loop and planner refuse with "Set the stack commands in project.yaml first". Unset gates are skipped. `try_command`/`run_process` take a cancel event.
- Merge presets: `direct_unless_risky` = defaults, `always_pr` = `protected_paths: ['**']`, `always_direct` = `max_diff_lines: 100000` + `protected_paths: []`.
- Desktop: the old dialog's model adapted to the job API (UI unchanged until T36); the panel shows the `no_commands` reason.
- Tests: each source end to end, a forced failure after every step for every source (tree and git state unchanged), an empty folder kept, symlinks not followed, cancel during commands, a failing test command (`commands.test`, first failure line), path, template and name refusals with no job, presets and their decisions, CLI and API workspaces identical, 1 h retention.
- Docs: `api.md` (creating a project, rollback, presets), `templates.md`, `project-yaml.md`, `architecture.md`, README, `task.md`; DECISIONS 337–344.

## T36 · New project dialog

- Daemon: `GET /api/templates` adds `commands` (`install`, `lint`, `test` from the contract); a job's `commands` step adds `passed`. While a running job holds a project, the list and detail answer `run_state: "creating"` with `job_id` and read nothing else (no `project.yaml` validation, no run log). TS client regenerated.
- CLI: `spool init --template` takes a built-in name, a local folder or a git URL again, plus `--template-ref` and `--branch` (template or empty repo, default `main`; refused for an existing repo with "An existing repo uses its checked-out branch"), through a CLI-only `Local` option on `check_request`; `CreateProject` is unchanged and the API still refuses a folder or URL. Folder and URL templates pass `check_safe`; step 2 renders the commit step 1 resolved; `template.name` is the contract's name.
- Desktop: `features/project-create` rewritten to D1 (560 px, ✕): source switch, template cards with Bundled badge, name with live slug check, workspace path, repo folder with picker and per-source help, stack commands (pre-filled / "e.g. just test" / optional), "More" (remote, merge preset, ClickUp list); Create posts, 422 errors at their field; checklist polled every 500 ms (stops on close) with icon + label per step and "n of 3 passed"; failure shows message, output and rollback, **Fix** focuses the failed field; Cancel and close ask first, then cancel; success opens the panel on Spec with the toast "Project created — write your spec next" (new shared `showToast`/`Toaster`). Home shows "Creating…" and no Needs-you card or event stream for such a project. The two-step dialog and its placeholder commands are gone.
- Tests: daemon (template commands, `creating` not validated, gone after rollback, `passed`, CLI folder/git-URL/unsafe templates, `--branch dev`, `--branch` with an existing repo, bad branch, API 422 for folder/URL and unknown `template_ref`/`branch`), Vitest (fields and help per source, `VW`, pre-filled commands, empty repo without commands, 422 at its field, step states, failure output and Fix focus, left-behind line, Cancel confirm, success navigation and toast, polling stops on close, templates Retry, Home "Creating…").
- Docs: `api.md` (template `commands`, `passed`, a project being created), `templates.md`, README (`spool init` options); DECISIONS 345–349.

## Chore · T36 follow-ups

- Daemon: an ended creation job whose rollback left paths is listed by `GET /api/projects` as `run_state: "cleanup_failed"` with `job_id` and `left` (kept 1 h); `POST /api/jobs/{id}/dismiss` forgets it. TS client regenerated.
- Desktop: Home shows such a project only as a Needs-you card "Couldn't clean up <name>" with the paths and **Dismiss**; a Cancel whose rollback leaves something shows an error toast. The panel of a project being created shows "Creating…" and the job's live checklist, nothing else; it opens on Spec on success and says "This project wasn't created" with **Back to Home** on failure or cancel.
- A real failing `test` command (a script printing `FAILED test_example`, exit 1) shows its own output in the failed step for every source; no fix was needed.
- Tests: daemon (left paths listed and dismissed, clean rollback not listed, running job not dismissed, a read-only repo the rollback can't delete, the real failing command per source), Vitest (Needs-you card and Dismiss, cancel toast, panel creating / success on Spec / failure).
- Docs: `api.md` (rollback left behind, dismiss, the panel while creating); DECISIONS 350–351.

## T21 · Tickets tab and plan review

- Plan: T21 split into T21 (this, 2.5 h) and T37 · Ticket drawer and actions (2.5 h, depends on T21); T23 depends on T37; 36 tickets, 86.5 h; critical path T01 → T02 → T04 → T05 → T06 → T13 → T19 → T20 → T32 → T33 → T34 → T35 → T36 → T21 → T37 → T23 → T26 (38 h).
- Daemon: `GET /api/projects/{name}/plan` (`services/planner/overview.py`): `state` (`none`, `planning` from the live plan job, `draft`, `approved`), `generated_at`, `ticket_count`, `total_h`, `problems` (`invalid_ticket`, `unknown_dependency`, `cycle` with its members in order, `duplicate_id`, `missing_done_when`). `POST …/plan/approve` raises `PlanInvalid` → 409 `plan_invalid` with `problems`, nothing written. `GET …/tickets` items carry `activity` (attempts, usage, latest run id and reason) from one grouped query. TS client regenerated.
- Desktop: `entities/plan` (plan queries; generate moved from the Spec tab), ticket status badge and chip, `widgets/ticket-list` (search, phase filter, Show done; draft banner with counts, problems as links, **Approve plan** through D4 with tickets, phases, estimate, review-required and first up, disabled with "Fix n problems first"; **Re-plan** through its confirm; groups Draft · Needs approval · Blocked · Running · Ready · Done, empty hidden, Done collapsed; rows with chip, title, **Next**, phase, dependency chips solid/outlined, estimate, review icon, attempts, usage, status, reason and problem line; no-spec, no-plan, planning, no-match, loading and error states), `widgets/ticket-drawer` (520 px, `?ticket=`, Esc/✕, Scope, Done when with the latest review per item, Dependencies, Details, "no longer exists"). No Cancel planning: no endpoint.
- `remark-gfm` 4.0.1 in the shared Markdown (tables, disabled task-list checkboxes; raw HTML and `javascript:` still inert).
- Line limit covers `desktop/src-tauri/src/**/*.rs`; Clippy `too_many_lines` on (default 100). Nothing was over.
- Tests: daemon (summary none/planning/draft/approved, each problem's code and ids, invalid file, approve 409 with files unchanged, clean approve, ticket activity, a fixture `.rs` over 500 lines), Vitest (groups and Next, dependency chips, search/phase/Clear filters, banner counts, Approve disabled and through the confirm, Re-plan confirm, each empty state, loading and Retry; drawer from a row and a problem link, reload, Esc, ✕, dependency chip, unknown id, review per item; GFM checklists and tables; Done-when splitting).
- Docs: `api.md` (plan summary, `activity`, `plan_invalid`), `planner.md`; DECISIONS 352–358.
