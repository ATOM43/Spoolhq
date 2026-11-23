# Agent Orchestrator — Ticket Plan

Oct 17, 2026 · @Atom

## Overview

The app turns a written task spec into an approved ticket plan, then has one coding agent implement the tickets in dependency order. Each ticket reaches main only after tests and an independent review pass. v1 is **51 tickets in 6 phases, about 112.5 hours** for one developer.

**What v1 includes**

- Projects as folders, like Claude Projects: the spec (`CONTEXT.md`), settings (`project.yaml`), tickets as markdown files, and a log of every agent run.
- A planner agent that splits the spec into tickets. You approve the plan before anything runs.
- Reusable stack templates (Copier), so every generated project starts with the same layout and the same `install`, `test` and `lint` commands.
- One agent at a time, running directly on your machine in a git worktree.
- Local git first. With GitHub configured, simple tickets merge into main and push; review-required tickets open a pull request and wait for you.
- One-way sync of tickets to ClickUp.

**Not in v1** (see Later phases): Docker isolation, parallel agents, Jira, two-way tracker sync.

**The parts**

- **Daemon** (Python, FastAPI): owns projects, the run loop, git and the tracker. Keeps running when the window closes, and runs headless on a server.
- **CLI** (`orch`, Typer): every action without the UI. It is how the tool builds itself from Phase 3 on.
- **Desktop app** (Tauri 2, React, TypeScript): a view and control panel over the daemon's API.
- **Agent runtime**: an `AgentRunner` interface, with adapters for the coding CLIs people already pay for (Claude Code by default, Codex), so a subscription is enough; the Claude Agent SDK covers API keys.

**How the tickets are sliced** (same rules as the dashboard plan)

- Loop before UI: the run loop is the product, the app is a window onto it.
- One ticket = one branch = one pull request, merged before the next starts.
- Each ticket is 1.5 to 4 hours and ends with a "Done when" checklist.

**Build it with itself.** After T14 the tool can take one ticket from ready to merged. From T15 on, write each ticket as a file and let the orchestrator implement it while you review. Every failure it hits becomes a bug report for the next ticket.

## Prior art

Several open-source tools cover parts of this, and Kontora comes close to the run loop. None combines a spec-to-plan step, reusable stack templates, an autonomous dependency-ordered loop with a merge policy, and ClickUp sync. That combination is the reason to build it.

| Tool | What it does | Missing for this project | Licence |
| --- | --- | --- | --- |
| [Kontora](https://github.com/worksonmyai/kontora) | Markdown tickets run through implement → review → fix → commit pipelines; one worktree per ticket; TUI and web board | Planner from a spec, stack templates, tracker sync | Apache-2.0 |
| [Task Master](https://github.com/eyaltoledano/claude-task-master) | Parses a PRD into tasks with dependencies; CLI and MCP server | Does not run, check or merge anything | MIT + Commons Clause |
| [OpenAI Symphony](https://github.com/openai/symphony) | Polls Linear, runs one agent per issue in its own workspace, opens a PR | Linear only; no planning step | Apache-2.0 |
| [Vibe Kanban](https://github.com/BloopAI/vibe-kanban) | Kanban board; each card runs an agent in its own branch, terminal and dev server | You drive each card; no autonomous loop. Company shut down April 2026, now community-maintained | Apache-2.0 |
| [Claude Squad](https://github.com/smtg-ai/claude-squad) | Terminal manager for several agent sessions in tmux and worktrees | No tickets, plan or merge policy | AGPL-3.0 |

**Worth borrowing**

- Ticket files with YAML frontmatter, as Kontora does, so tickets stay readable and diffable.
- Symphony's agent policy kept in a versioned file inside the repo (`WORKFLOW.md`).
- Vibe Kanban's split between a task and its attempts, which maps onto tickets and runs here.

**Before T01:** spend two hours running Kontora on the dashboard spec. If its pipeline already covers Phase 2, build the planner, templates and tracker on top of it instead; Apache-2.0 allows that. Task Master's Commons Clause forbids competing products built on it, so it is not a base.

## Ticket map

Work top to bottom in ticket order; with one developer the order matters more than the critical path. Milestone M1 (self-hosting) comes after T14, M2 (v0.1.0 release) after T26.

&#91;embedded content: v1 roadmap · 6 phases, 2 milestones\]

The CLI and run loop come first, so from Phase 3 on the orchestrator writes its own code; the UI follows once there is something worth watching.

| ID | Ticket | Phase | Depends on | Est. \[h\] |
| --- | --- | --- | --- | --- |
| T01 | Repository and tooling | 0 Scaffolding | — | 2 |
| T02 | Daemon and CLI scaffold | 0 Scaffolding | T01 | 1.5 |
| T03 | Desktop shell | 0 Scaffolding | T02 | 2.5 |
| T04 | Project workspace and settings | 1 Project model | T02 | 2 |
| T05 | Ticket file format and store | 1 Project model | T04 | 2.5 |
| T06 | Dependency graph and scheduler | 1 Project model | T05 | 2 |
| T07 | Run log and event bus | 1 Project model | T02 | 2 |
| T08 | Git workspace manager | 2 Run loop | T04 | 2.5 |
| T09 | Agent runner and Claude Code CLI | 2 Run loop | T02 | 3 |
| T10 | Context pack and prompts | 2 Run loop | T05, T09 | 2 |
| T11 | Quality gates | 2 Run loop | T04 | 2 |
| T12 | Reviewer agent | 2 Run loop | T09, T11 | 2.5 |
| T13 | Run loop | 2 Run loop | T06, T07, T08, T10, T11, T12 | 3.5 |
| T14 | Local integration | 2 Run loop | T13 | 2.5 |
| T15 | Planner agent | 3 Planner and Git | T06, T09 | 3.5 |
| T16 | Template library | 3 Planner and Git | T04, T11 | 3.5 |
| T17 | GitHub delivery | 3 Planner and Git | T14 | 3.5 |
| T18 | Merge policy | 3 Planner and Git | T12, T17 | 1.5 |
| T19 | Live API | 4 Desktop UI | T07, T13 | 2.5 |
| T20 | Event bridge, Home and New project | 4 Desktop UI | T03, T19 | 2 |
| T21 | Tickets tab and plan review | 4 Desktop UI | T15, T36 | 2.5 |
| T22 | Live run | 4 Desktop UI | T37 | 2 |
| T23 | Bundled daemon | 4 Desktop UI | T21, T40, T36, T37, T41, T42, T43, T44, T45, T46, T47, T48, T51 | 2 |
| T24 | Tracker adapter and ClickUp | 5 Release | T05, T14 | 3 |
| T25 | Dogfood on the dashboard task | 5 Release | T16, T18, T21, T40 | 3 |
| T26 | Documentation and release | 5 Release | T50, T52, T25 | 2.5 |
| T27 | Agent roles, custom endpoints and contract suite | 3 Planner and Git | T09, T14 | 2 |
| T30 | Codex CLI backend | 3 Planner and Git | T27 | 2 |
| T31 | Claude Agent SDK backend | 3 Planner and Git | T27 | 2 |
| T28 | Code graph with Graphify | 3 Planner and Git | T14, T16 | 2.5 |
| T32 | Settings, project panel and Spec tab | 4 Desktop UI | T20 | 2 |
| T33 | Home and project panel polish | 4 Desktop UI | T32 | 2 |
| T34 | Settings polish and secret test | 4 Desktop UI | T33 | 1.5 |
| T35 | Project creation job | 4 Desktop UI | T34, T16 | 2 |
| T36 | New project dialog | 4 Desktop UI | T35 | 2 |
| T37 | Ticket drawer and actions | 4 Desktop UI | T21 | 2.5 |
| T38 | Add ticket | 4 Desktop UI | T37 | 1.5 |
| T39 | Run details | 4 Desktop UI | T22 | 2 |
| T40 | Past runs and replay | 4 Desktop UI | T39 | 2 |
| T41 | Draft tickets with the planner (daemon and CLI) | 4 Desktop UI | T38, T15 | 2 |
| T42 | Repo safety | 4 Desktop UI | T36 | 1.5 |
| T43 | Existing repo onboarding | 4 Desktop UI | T42 | 2.5 |
| T44 | Drafting in the form | 4 Desktop UI | T41 | 2 |
| T45 | Agent notes written by code | 3 Planner and Git | T14, T16 | 1.5 |
| T46 | Notes layout in templates and old projects | 3 Planner and Git | T45 | 2 |
| T47 | Project settings: agents | 4 Desktop UI | T32, T27 | 2 |
| T48 | Quality gates for projects | 3 Planner and Git | T46 | 2 |
| T49 | Background running and tray | 4 Desktop UI | T23 | 1.5 |
| T50 | Installers and update feed | 4 Desktop UI | T49 | 2.5 |
| T51 | Tracker sync in the app | 4 Desktop UI | T24, T33 | 1.5 |
| T52 | Update check in the app | 4 Desktop UI | T50 | 1.5 |
|  | **Total** |  |  | **112.5** |

Critical path, if tickets ran in parallel: T01 → T02 → T04 → T05 → T06 → T13 → T19 → T20 → T32 → T33 → T34 → T35 → T36 → T21 → T37 → T22 → T39 → T40 → T23 → T49 → T50 → T52 → T26 (48.5 h).

## Phase 0 — Scaffolding

Three tickets get the daemon, CLI and desktop shell running and talking to each other. No orchestration logic yet.

### T01 · Repository and tooling

The repo every later ticket builds on, open source from the first commit. *Depends on: nothing · 2 h*

- Monorepo: `daemon/` (Python), `desktop/` (Tauri + React), `templates/`, `docs/`, `README.md`, `DECISIONS.md`, `LICENSE` (Apache-2.0).
- Python: uv, ruff, mypy, pytest. TypeScript: pnpm, ESLint, Prettier, Vitest.
- A `justfile` with `install`, `dev`, `test`, `lint`.
- GitHub Actions running lint and tests on Linux, macOS and Windows.
- `CONTRIBUTING.md` and issue templates.

Done when:

- [ ] `just install && just test` passes on a clean clone
- [ ] CI is green on all three operating systems

### T02 · Daemon and CLI scaffold

A daemon that starts and answers, and a CLI that talks to it. *Depends on: T01 · 1.5 h*

- FastAPI app with `GET /api/health`; settings from `~/.orch/config.toml` and environment variables.
- Typer CLI `orch` with `orch serve` and `orch version`; other commands call the daemon's API.
- Binds to 127.0.0.1 only and requires a random token stored in the config folder.
- Structured logs in `~/.orch/logs/`.

Done when:

- [ ] `orch serve` starts the API and `/docs` shows it
- [ ] A request without the token is rejected

### T03 · Desktop shell

A Tauri window that reaches the daemon. *Depends on: T02 · 2.5 h*

- Tauri 2, React, Vite, TypeScript, Tailwind, shadcn/ui, TanStack Query.
- In development the app connects to a running daemon; bundling it comes in T23.
- Empty routes: Projects, Project board, Run, Settings.
- A typed fetch helper that turns non-2xx responses and a missing daemon into readable errors.

Done when:

- [ ] The window shows "Daemon: ok"
- [ ] With the daemon stopped, the app says how to start it instead of showing a blank window

## Phase 1 — Project model and ticket store

Four tickets define what a project and a ticket are, on disk and in the database. Everything later reads and writes through these.

### T04 · Project workspace and settings

One folder per project, with validated settings. *Depends on: T02 · 2 h*

- `orch init <name> --repo <path>` creates `~/orch-projects/<name>/` with `project.yaml`, `CONTEXT.md`, `tickets/` and `runs/`.
- `project.yaml` validated by Pydantic: repo path, default branch, stack commands (`install`, `test`, `lint`), agent model and budget, retry limits, merge policy, optional GitHub remote, optional tracker.
- Errors name the field, for example `project.yaml: git.remote: not a GitHub URL`.
- Code-facing notes (`PROGRESS.md`, `DECISIONS.md`, `CLAUDE.md`) live in the repo, because agents read them alongside the code.

Done when:

- [ ] `orch init` on an existing repo creates a valid workspace
- [ ] One test per required field shows a readable error when it is missing

### T05 · Ticket file format and store

Tickets as markdown files people and agents can both read. *Depends on: T04 · 2.5 h*

- One file per ticket: YAML frontmatter (`id`, `title`, `phase`, `depends_on`, `status`, `estimate_h`, `review_required`, `tracker_ref`) and a body with scope and "Done when".
- Read and write back without reordering the body or losing text the user added.
- Statuses: draft, ready, running, awaiting\_approval, blocked, done.
- `orch tickets list | show | edit`, filtered by status and phase.

Done when:

- [ ] Round-trip test: reading then writing leaves every fixture file byte-identical
- [ ] The 18 tickets of the dashboard plan load from hand-written files

### T06 · Dependency graph and scheduler

Decides what runs next and refuses broken plans. *Depends on: T05 · 2 h*

- Validate the graph: unknown dependency, cycle, duplicate id, each named in the error.
- `next_ready()`: the lowest-numbered ticket whose dependencies are all done.
- Allowed status transitions as a table; any other transition raises.
- Critical path and remaining hours for the UI.

Done when:

- [ ] Tests: a cycle is reported with its members; blocked cannot jump to done
- [ ] On the dashboard plan, `next_ready()` returns T01, then T02 once T01 is done

### T07 · Run log and event bus

A record of every attempt that survives crashes. *Depends on: T02 · 2 h*

- SQLite in the workspace (`.orch/state.db`): runs, attempts, append-only events, token cost.
- Each attempt keeps its transcript, gate output, diff and review verdict under `runs/<ticket>/<attempt>/`.
- An in-process event bus; the API streams it from T19.
- On startup, runs left running by a crash are marked interrupted.

Done when:

- [ ] Killing the daemon mid-run and restarting shows the run as interrupted, not running
- [ ] Every attempt's files can be found from its database row

## Phase 2 — Single-agent run loop

Seven tickets take one ticket from ready to merged with no human in the loop. This phase is the product and gets the most tests. It ends at milestone M1: the tool can implement its own remaining tickets.

&#91;embedded content: run loop for one ticket · T08–T14, with the T18 merge policy\]

Gates and review each loop back to the implementer with their findings; only a ticket that passes both, and trips no merge-policy rule, merges without you.

### T08 · Git workspace manager

A clean, disposable working copy per attempt. *Depends on: T04 · 2.5 h*

- Refuse to start when the main repo has uncommitted changes, and list the files.
- One worktree per attempt from the latest default branch, on `feat/T04-<slug>`, under `~/.orch/worktrees/<project>/`.
- Every git call as an argument list, never through a shell; ticket text can contain anything.
- Teardown always runs; on startup, worktrees left by a crash are listed and pruned.

Done when:

- [ ] Tests on a temporary repo: create, commit, teardown, and recovery after a simulated crash
- [ ] A ticket title containing quotes and `;` produces a valid branch name

### T09 · Agent runner and Claude Code CLI

One interface for running a coding agent, with the user's own Claude Code CLI as the first backend, so a subscription is enough. *Depends on: T02 · 3 h*

- `AgentRunner.run(prompt, cwd, policy, max_turns, budget)` streams normalised events (message, tool call, file edit, usage) and returns a summary, files changed and usage.
- First adapter drives the installed `claude` CLI in headless mode with streaming JSON output, started with an argument list inside the worktree. Check the current flags in its docs.
- Policy translation: worktree-only file access and the shell allowlist (stack commands plus read-only git) are written into the CLI's own permission settings for that run. A backend that cannot enforce the policy is refused; never skip-permissions.
- Usage: subscription runs report tokens and turn a usage-limit error into a pause until the reset time; API runs report cost.
- `spool agents` lists detected backends, versions and login status. Timeout and cancel. A fake runner replays recorded transcripts for tests.

Done when:

- [ ] A real run through the `claude` CLI creates a file in a scratch repo; the same run passes in CI with the fake runner
- [ ] A command outside the allowlist is denied and logged
- [ ] A usage-limit error pauses the run with the reset time instead of failing the ticket

### T10 · Context pack and prompts

What the implementer knows when it starts. *Depends on: T05, T09 · 2 h*

- The prompt combines the ticket, the relevant spec section, `PROGRESS.md`, `DECISIONS.md`, the repo's `CLAUDE.md`, and the last attempt's failures.
- Prompts are Jinja files in the repo, versioned and overridable per project.
- A size budget trims long inputs and notes what was cut.
- The agent ends by writing a short progress entry, which the orchestrator adds to `PROGRESS.md` at merge.

Done when:

- [ ] Snapshot tests of the rendered prompt for a fixture ticket
- [ ] A retry prompt contains the exact failing test names from the previous attempt

### T11 · Quality gates

Deterministic checks that run before any review. *Depends on: T04 · 2 h*

- Run the project's `install`, `lint` and `test` commands in the worktree, each with a timeout.
- A structured result per command: pass or fail, duration, trimmed output that keeps the failing part.
- A "Done when" line can name a command (`` `just test` passes ``); the gate checks it, not the reviewer.
- Gates are code, not an agent: the same input always gives the same result.

Done when:

- [ ] Tests: a failing test, a lint error and a timeout each give the right structured result
- [ ] 50,000 lines of output are trimmed but keep the first failure

### T12 · Reviewer agent

A second opinion that never saw how the code was written. *Depends on: T09, T11 · 2.5 h*

- Fresh context: the ticket, the diff and the gate results, never the implementer's transcript.
- Read-only tools.
- Returns schema-checked JSON: each "Done when" item met or not met with a reason, then approve, changes\_requested or needs\_human.
- An invalid response is retried once, then treated as needs\_human.

Done when:

- [ ] Fake-runner tests cover all three verdicts and an invalid response
- [ ] On a seeded diff that skips one "Done when" item, the reviewer names that item

### T13 · Run loop [Done]

The state machine that ties T08 to T12 together. *Depends on: T06, T07, T08, T10, T11, T12 · 3.5 h*

- Worktree → implementer → gates → retry with the errors (up to 3) → reviewer → fix with the review notes (up to 2) → integrate.
- Limits used up, or a needs\_human verdict: the ticket is blocked and its worktree kept for inspection.
- One run at a time per project, enforced by a lock; pause, resume and cancel.
- `orch run next` and `orch run all`, which stops at the first blocked ticket.

Done when:

- [ ] Fake-runner tests for the happy path, a gate retry, a review retry and the blocked path
- [ ] Cancel during a run removes the worktree and puts the ticket back to ready

### T14 · Local integration

Getting a finished attempt into main safely. *Depends on: T13 · 2.5 h*

- The orchestrator commits, not the agent: `T04: <title>` with a trailer linking the run.
- Rebase onto the current main, rerun the gates, squash-merge, tag `ticket/T04`.
- A rebase conflict goes back to the implementer once, with the conflict; a second conflict blocks the ticket.
- The progress entry is added to `PROGRESS.md` in the same commit.

Done when:

- [ ] Running a 3-ticket fixture project gives 3 commits on main, each with green gates
- [ ] main is never left mid-rebase, even when the daemon is killed during integration
- [ ] **M1:** the orchestrator implements and merges one real ticket in its own repo

## Phase 3 — Planner, templates and GitHub delivery

Eleven tickets add the parts around the loop: turning a spec into tickets, starting projects from templates, delivering through GitHub, more agent backends, the code graph, agent notes written by code, that notes layout in templates and old projects with a file-size gate for every project, and quality gates that keep weakened tests, secrets and unreviewed dependencies off main. From here the orchestrator implements its own tickets while you review.

### T15 · Planner agent

From a spec to a ticket plan you approve. *Depends on: T06, T09 · 3.5 h*

- Reads `CONTEXT.md` and the chosen template's description; writes draft tickets with scope, dependencies, estimate, "Done when" and `review_required`.
- Output is JSON checked against the ticket schema and the graph rules from T06, then written as draft files.
- Nothing runs until `orch plan approve`. Re-planning keeps tickets the user has edited.
- Planning rules (ticket size, one branch per ticket, tests in every ticket) live in an editable prompt file.

Done when:

- [ ] Given the dashboard spec, the plan validates with no cycles and every ticket has a "Done when"
- [ ] A ticket the user edited survives a re-plan unchanged

### T16 · Template library

The same proven structure for every new project, instead of regenerating boilerplate. *Depends on: T04, T11 · 3.5 h*

- Templates are Copier projects from a local folder or a git URL. Unlike cookiecutter, Copier can update a project when its template improves.
- `orch init --template fastapi-react` generates the repo and fills the stack commands in `project.yaml`.
- First template: FastAPI, SQLAlchemy and pytest; React, Vite and TypeScript; a `justfile` with `install`, `dev`, `test`, `lint`; a `CLAUDE.md` with conventions; CI.
- Contract check: a template must declare its commands, and they must pass on a freshly generated project.
- The planner treats "apply template" as already done, so plans start at real work.

Done when:

- [ ] A generated project passes its own gates with no agent involved
- [ ] A template without a `test` command is rejected with a clear message

### T17 · GitHub delivery

Local git first; GitHub when the project has a remote. *Depends on: T14 · 3.5 h*

- Direct mode: after a local merge, push main.
- PR mode: push the branch and open a pull request whose body holds the ticket, gate results and review verdict. The ticket waits in awaiting\_approval.
- Poll the PR: merged → pull main and mark done; changes requested → the comments start a new attempt; closed → blocked.
- The token comes from the OS keychain or an environment variable and is never written into the workspace.

Done when:

- [ ] Against a test repo: one ticket merged directly, one through a merged PR, one through a PR with requested changes
- [ ] A failed push blocks the ticket and shows the git error

### T18 · Merge policy

Decides which tickets merge directly and which need you. *Depends on: T12, T17 · 1.5 h*

- A ticket goes through a PR when any rule holds: `review_required` set by the planner or user; diff larger than a set number of lines; protected paths touched (for example migrations, CI, auth); reviewer verdict needs\_human.
- Without a GitHub remote, the same rules pause for approval in the app.
- Every decision is logged with the rule that triggered it.

Done when:

- [ ] Tests: each rule on its own sends a ticket to a PR
- [ ] The run log names the rule behind each PR

### T27 · Agent roles, custom endpoints and contract suite

The shared parts every backend needs. Numbered T27 so existing IDs stay fixed. *Depends on: T09, T14 · 2 h*

- `project.yaml` picks a backend per role (planner, implementer, reviewer), with `agents.default` as the fallback.
- Each backend takes an optional `base_url` and `model`, so a local model server (for example Ollama) can be used later without code changes. Plain http only for localhost.
- One contract test suite every adapter must pass: recorded transcripts in CI, installed CLIs locally.
- `spool agents --project <name>` shows which backend each role uses.

Done when:

- [ ] Planner, implementer and reviewer can each use a different backend
- [ ] Each backend accepts a custom `base_url` and `model`
- [ ] The contract suite passes for every adapter

### T30 · Codex CLI backend

Codex CLI behind the same interface. *Depends on: T27 · 2 h*

- Adapter for Codex exec mode with JSON events, mapping the policy onto Codex's own sandbox and approval settings through a per-run config, never the user's own.
- A policy part Codex can't enforce is refused with a clear message; no fallback to weaker modes.
- Usage with Codex's own cache weighting; usage limits pause the run.
- Check OpenAI's terms for driving Codex with a subscription login; record in DECISIONS.md.

Done when:

- [ ] The same ticket fixture runs end to end on Codex (recorded in CI)
- [ ] A backend that cannot enforce the policy is refused with a clear message

### T31 · Claude Agent SDK backend

The Claude Agent SDK behind the same interface, for users with an API key. *Depends on: T27 · 2 h*

- Claude Agent SDK adapter for API keys, with the allowlist enforced by a hook; key from the environment or keychain, never a subscription login.
- Passes T27's contract suite.

Done when:

- [ ] The adapter passes the contract suite
- [ ] The API key never appears in argv, logs or files

### T45 · Agent notes written by code

Make SpoolHQ the only writer of a project's notes files. *Depends on: T14, T16 · 1.5 h*

- The implementer returns, in its final message as today, a structured run note: `progress` (one entry, 1 to 1,500 characters) and `decisions` (0 to 5, each with `area`, `title` of one line up to 100 characters, and `text` up to 2,000 characters). SpoolHQ cleans every field first: control characters removed, no newline or ` · ` in a title, a text line starting with `#` indented by one space. The prompt says to put progress and decisions only in the note and never to edit the notes files, overriding the repo's own `CLAUDE.md`. A missing or unreadable note fails the attempt with "The agent didn't return its run note", retried like a gate failure.
- Areas come from `notes.decision_areas` in `project.yaml`, default `[general, api, data, ui, infra, testing]`; an unknown area fails the attempt with "Unknown decision area '<x>'; use one of: …", counted against the gate retries.
- A diff (against the merge base) that adds or changes `PROGRESS.md`, `DECISIONS.md`, `docs/progress-archive.md` or anything under `docs/decisions/` fails the policy step with "The agent edited notes files: <file>; put progress and decisions in the run note instead" and goes back to the agent as a retry.
- At merge, in the same commit and under the run lock, SpoolHQ writes the notes, byte-exact outside what it adds: the entry `### T07 · <title> (<date>)` at the top of `PROGRESS.md`'s managed part between `<!-- spoolhq:recent:start -->` and `<!-- spoolhq:recent:end -->` (markers added at the end on the first merge), the newest 5 kept there and older ones moved word for word to the end of `docs/progress-archive.md`; each decision as `NNN. <title>` with its text indented in `docs/decisions/<area>.md` plus `NNN · <title> · docs/decisions/<area>.md` in the `DECISIONS.md` index (split layout), or appended to a flat `DECISIONS.md` in the same format.
- A notes check before the integration commit (a service, for T46 too): every index line matches exactly one entry and the reverse, numbers have no gaps or duplicates, titles match; a failure blocks the ticket with "The notes files don't match: <first problem>".
- The dev fake runner returns a structured note in every implementer scenario.

Done when:

- [ ] Plan.md lists T45 and T46, with consistent table, totals and critical path
- [ ] After many merges, PROGRESS holds the newest 5 entries and nothing is lost
- [ ] Each decision lands in its area file with an index line, written by code
- [ ] An agent diff touching the notes files goes back to the agent as a retry
- [ ] Lint and tests pass, and CI is green on Linux, macOS and Windows

### T46 · Notes layout in templates and old projects

Start new projects with the split notes layout, convert old flat ones, and hold file size in every project. *Depends on: T45 · 2 h*

- Template (fastapi-react): `PROGRESS.md` with a short summary heading and the empty `spoolhq:recent` markers; `DECISIONS.md` with the index header and no entries, plus `docs/decisions/.gitkeep`; a rules-only `CLAUDE.md` saying progress and decisions go in the run note, never into the notes files; `notes.decision_areas` with the default list in the generated `project.yaml`. The template's contract check also runs the notes check, so a freshly generated project passes it before any ticket runs.
- File size as a built-in gate: `gates.max_file_lines` in `project.yaml` (default 500, 0 turns it off) checks only text files the ticket added or changed, counted like SpoolHQ's own script. A changed file must stay within the limit, unless it was already over before the ticket and didn't grow. Lockfiles, minified files and `gates.max_file_lines_exempt` (globs, default `["**/*.lock", "**/*-lock.*", "**/*.min.*"]`) are exempt. It runs after lint and test and fails with "<path>: 612 lines, over the 500-line limit" or "<path> grew from 640 to 655 lines; it was already over the limit", back to the implementer like any gate failure. The Gates panel shows it as its own row, "File size". A template's own line check stays.
- Old flat projects are converted on their first merge, before the new notes are written, in the same commit: PROGRESS without markers keeps everything and gets the markers at the end; a flat `DECISIONS.md` has every entry moved word for word into `docs/decisions/general.md` in the T45 format, keeping its number (unnumbered entries numbered in order of appearance), and becomes the index. The notes check runs afterwards; a file that can't be parsed into entries blocks the ticket with "DECISIONS.md couldn't be converted: <reason>" and changes nothing. The commit body records the conversion.
- SpoolHQ's own `scripts/check_decisions.py` also fails when `PROGRESS.md` holds more than 5 recent entries: "PROGRESS.md has 7 recent entries; move the oldest to docs/progress-archive.md".

Done when:

- [ ] Plan.md lists the extended T46 and T47, with consistent table, totals and critical path
- [ ] A project generated from the template passes the notes check before any ticket runs
- [ ] A flat project is converted on its first merge with every entry kept word for word
- [ ] A ticket that makes a file too long fails its gates in every project, including existing repos
- [ ] SpoolHQ's own lint fails when PROGRESS has more than 5 recent entries
- [ ] Lint and tests pass, and CI is green on Linux, macOS and Windows

### T48 · Quality gates for projects

Stop weakened tests, leaked secrets and unreviewed dependencies from reaching main. *Depends on: T46 · 2 h*

- A built-in **test guard** gate: fails when the ticket's diff deletes test files or test functions, adds skip markers (`pytest.mark.skip`, `xfail`, `.skip(`, `.only(`), or lowers coverage below the base branch's, unless the ticket's "Done when" explicitly names the removal.
- A built-in **secret scan** of the diff: common key and token patterns and high-entropy strings in added lines; a hit fails the gate and never prints the secret itself.
- **New dependencies** in a lockfile or manifest send the ticket to approval through the merge policy, with the rule "Adds dependencies: <names>".
- The fastapi-react template's `just lint` gains what SpoolHQ uses on itself, where missing: mypy strict, ruff `S`, the UTF-8 rule, layer rules, and a coverage floor.

Done when:

- [ ] A ticket that deletes or skips a test fails the test guard
- [ ] A ticket that adds an API key fails the secret scan without printing it
- [ ] A ticket that adds a dependency waits for approval

## Phase 4 — Desktop UI (v0 screens)

Twenty-three tickets put a minimal face on the daemon, package it and keep it up to date: two screens (Home and the project panel, with its Settings tab), a ticket drawer and three dialogs, as specified in `screens-prompt-v0.md`. The full 16-screen design in `screens-prompt.md` is the v0.2 target. Everything here already works from the CLI.

### T19 · Live API

What the app reads, and a live stream of what the agent is doing. *Depends on: T07, T13 · 2.5 h*

- REST endpoints for projects, tickets, runs and settings; a WebSocket stream of run events.
- A TypeScript client generated from the OpenAPI schema.
- Paged run history; ETags so a ticket edited in a file and in the app at once is never overwritten silently.

Done when:

- [ ] API tests for every endpoint, including a conflicting edit
- [ ] A test client receives every event of a fake run, in order

### T20 · Event bridge, Home and New project

Live events in the app, the project list and project creation. *Depends on: T03, T19 · 2 h*

- Event stream through Rust: commands that open the daemon WebSocket, authenticate and forward each event to the webview over a Tauri channel, reconnecting with `since`; the token never enters the webview.
- Query hooks for projects, tickets, runs and agents; run events update them, no polling while the stream is up.
- Home: project list with progress and status, a "Needs you" section, and an empty state that opens New project.
- New project dialog: name, repo path or template, the three stack commands with **Test**.
- A daemon-not-running state on Home instead of a blank window, which recovers by itself.

Done when:

- [ ] Run events reach the app through Rust; the token never enters the webview
- [ ] From Home, create a project from a repo path or template, with each stack command tested, without touching the CLI
- [ ] Home shows empty, loading, error and daemon-missing states

### T32 · Settings, project panel and Spec tab

The setup dialog and the panel where a project is written and planned. *Depends on: T20 · 2 h*

- Settings dialog: detected backends with version and login status; write-only secrets (Anthropic key, GitHub and ClickUp tokens) in the keychain; opens on first run when no backend is ready.
- Project panel shell: header with progress line and run controls that change with state (disabled controls say why); tabs Spec, Tickets, Run.
- Spec tab: markdown editor with autosave via ETag/If-Match, a conflict dialog on 412, and **Generate plan**.

Done when:

- [ ] From a fresh install: set the key, create a project, write a spec and generate a plan without touching the CLI
- [ ] Every disabled control shows why and what to do

### T33 · Home and project panel polish

Bring Home and the project panel in line with the v0 design. *Depends on: T32 · 2 h*

- Home: full-width top bar (app name, daemon status, **Settings**, **+ New project**); Needs-you cards with status chip, project, ticket, reason, age and one action; 320 px project cards with template badge, progress, "13 of 18 done · 12 h left", status as icon + label, last activity and total usage.
- No "Unknown" status: Running / Paused · usage limit / Needs you (n) / Idle / No spec yet / No plan yet / Plan in draft / All done / Settings invalid. The daemon reports a `project.yaml` validation error (file, field, message), last activity and total usage per project instead of failing.
- Project panel: full width, compact header (breadcrumb, repo path with copy, branch, remote), a guidance line by project state, underlined tabs with counts, a red bar for invalid settings with **Reload**.
- Disabled controls look disabled and show their reason on hover and keyboard focus (CSP-safe tooltip).
- Spec toolbar: word count and **Import .md**, confirming before replacing a non-empty spec.

Done when:

- [ ] Home and the panel match the design PNGs, with the spec winning where they differ
- [ ] No project shows "Unknown"; an invalid `project.yaml` names the field on Home and in the panel
- [ ] Disabled controls look disabled and show their reason on hover and focus

### T34 · Settings polish and secret test

Bring Settings in line with the design and let each secret be tested. *Depends on: T33 · 1.5 h*

- Underlined tabs, ✕ and a footer with **Done**.
- The Agent SDK without a key is shown as optional, not a warning.
- Each secret as a password field with **Save**, **Test** and **Remove**.
- A daemon endpoint that tests a stored secret with one read-only call and returns only a fixed message.

Done when:

- [ ] Settings matches the design, with the spec winning where they differ
- [ ] Each secret can be tested without the value ever leaving the daemon

### T35 · Project creation job

The daemon creates a project from a template, an existing repo or an empty repo, step by step, and rolls back what it created on failure. *Depends on: T34, T16 · 2 h*

- `POST /api/projects` returns 202 with a job id. Body: `name` (`^[a-z][a-z0-9-]{0,39}$`), `source` (`template` / `existing` / `empty`), an absolute `repo_path`, `template` (a name from `GET /api/templates` only, no git URLs or local paths), `commands` (`install`, `lint`, `test`; optional for `empty`), optional `git_remote`, `merge_preset` and `clickup_list_id`. Validation errors return 422 with the field before any job starts; `spool init` uses the same service.
- Path safety: refuse `/`, the home folder, anything inside the projects folder, the worktrees folder or `~/.spoolhq`, symlinked targets, a dirty existing repo and a duplicate name.
- Steps: create workspace → prepare repo (Copier, check only, or `git init -b main`) → check commands through the gates (install 600 s, lint and test 300 s) → initial commit. Each step reports its state, duration and, on failure, a fixed message, trimmed output and the request field that caused it.
- Rollback on failure or cancel: delete only the paths the job created, in reverse order, never following symlinks; an existing repo is never touched. The outcome is recorded in the job.
- `GET /api/jobs/{job_id}` and `POST /api/jobs/{job_id}/cancel`; jobs are kept in memory for 1 hour after they end.
- Stack commands become optional in `project.yaml`; a project without a `test` command can't run tickets. Merge presets map onto `merge_policy`. `GET /api/templates` adds a one-line `summary`.

Done when:

- [ ] A project can be created from a template, an existing repo and an empty repo through the API
- [ ] A failing step rolls back everything SpoolHQ created and never touches an existing repo
- [ ] Unsafe paths and template sources are refused before any job starts

### T36 · New project dialog

Create a project from the app with a visible checklist. *Depends on: T35 · 2 h*

- Source switch **Template / Existing repo / Empty repo**; template cards.
- Name with slug check and workspace preview; repo folder picker; stack commands pre-filled.
- A collapsed **More** section: GitHub remote, merge preset, ClickUp list.
- A live create checklist with **Fix** and **Cancel** on failure.
- The old two-step flow removed.

Done when:

- [ ] A project can be created from each of the three sources without the CLI
- [ ] A failed step shows its error and output and returns to the field that caused it

### T21 · Tickets tab and plan review

Review the plan and see every ticket in one list. *Depends on: T15, T36 · 2.5 h*

- `GET /api/projects/{project}/plan`: `state` (`none`, `planning`, `draft`, `approved`), `generated_at`, `ticket_count`, `total_h` and `problems` (`{code, message, ticket_ids}`: cycle, unknown dependency, duplicate id, missing "Done when"); `POST …/plan/approve` answers 409 `plan_invalid` with the problems and changes nothing.
- Tickets tab: search, phase filter, "Show done"; a draft banner with counts, problems as links to their ticket, **Approve plan** behind a confirm (disabled while problems exist) and **Re-plan**.
- One list grouped Draft · Needs approval · Blocked · Running · Ready · Done (empty groups hidden, Done collapsed), the next ticket marked; empty, planning, loading and error states.
- A read-only ticket drawer (`?ticket=`): scope, "Done when" with the latest review result, dependencies and details.
- `remark-gfm` in the safe Markdown component; Rust files under the 500-line limit and Clippy's `too_many_lines`.

Done when:

- [ ] A plan with a cycle cannot be approved, and the problem links to the ticket
- [ ] Tickets are grouped by status, with the next ticket marked, and every row opens its drawer
- [ ] Markdown checklists and tables render; raw HTML still doesn't
- [ ] Rust files are covered by the line limit, and Clippy's `too_many_lines` passes

### T37 · Ticket drawer and actions

Act on one ticket: edit it, run it, unblock it or approve it. *Depends on: T21 · 2.5 h*

- The drawer's primary action by status (spec section 7 table); "Why it needs you", Attempts and Git sections.
- Editing when Draft, Ready or Blocked, with the ETag and a "Changed on disk · Reload · Keep mine" bar.
- One note-to-agent dialog, shared by Unblock and Request changes.
- **Approve and merge** through a confirm in local mode; the PR link in GitHub mode.

Done when:

- [ ] Edits round-trip to the ticket files and survive a reload
- [ ] Each status shows its one primary action, and every disabled action says why

### T38 · Add ticket

Add a ticket by hand from the Tickets tab. *Depends on: T37 · 1.5 h*

- **Add ticket** opens an empty drawer in edit mode; the daemon assigns the next free number.
- The same validation as a plan.
- Saved as Draft before approval, or Ready when appended to an approved plan.

Done when:

- [ ] A ticket added in the app appears as a file with the next free number
- [ ] A new ticket with an unknown dependency or a cycle can't be saved, and the error names the field

### T41 · Draft tickets with the planner (daemon and CLI)

Turn a few lines into one or more well-formed draft tickets, in the daemon and the CLI; the form is T44. *Depends on: T38, T15 · 2 h*

- `POST /api/projects/{project}/tickets/draft` with `{request}` (1 to 2,000 characters) starts a job (202, `job_id`): the planner role's backend in single-ticket mode, read-only, with the planner's policy and limits, given the request, the spec if it's real (starter text counts as none), the existing tickets' ids, titles and statuses, and the code map if Graphify is available, inside the context budget.
- Its own prompt file next to the planner's, editable the same way: tickets of 1.5 to 4 hours, work over 4 hours split into two or three tickets, each with scope, a "Done when" list ending with the project's test command, dependencies, estimate, review flag and phase.
- JSON with 1 to 3 drafts (`ref` `D1` to `D3`, `title`, `scope`, `done_when`, `depends_on` with existing ids or refs, `estimate_h`, `review_required`, `phase`); invalid JSON is retried once, then the job fails with "The planner's answer couldn't be read".
- Each draft is validated like a plan (schema, unknown dependencies, cycles across drafts and existing tickets, empty "Done when", estimate over 4 h); problems come back per draft as `{code, message, field}` and don't fail the job. No files are written; the result is kept 1 hour like other jobs, and Cancel stops the agent.
- Usage is recorded as a run of kind `draft`. The job refuses to start, with a reason the form can show, when no agent is ready, a run is going or planning is running.
- `POST /api/projects/{project}/tickets/batch` saves edited drafts under the shared ticket lock: real ids in draft order, refs rewritten, the whole set validated, all files written or none; same status rules as T38.
- `spool tickets draft` (request as an argument or from stdin) prints the drafts and their problems as markdown; `--save` saves them only when there are no problems.
- A `ticket-draft` fake-runner scenario: one draft, or two linked drafts when the request contains "split".

Done when:

- [ ] Plan.md lists T41, T44 and T45, with consistent table, totals and critical path
- [ ] A few lines produce one valid draft ticket, with no files written
- [ ] Work over 4 h is split into two or three drafts with dependencies between them
- [ ] An invalid draft comes back with its problems, and the CLI won't save it
- [ ] Saving several drafts writes all of them or none
- [ ] Lint and tests pass, and CI is green on Linux, macOS and Windows

### T22 · Live run

Watch the current run as it happens. *Depends on: T37 · 2 h*

- Daemon: the agent's messages, tool calls and results, file edits, usage, denials and stream warnings stored as run events; `step` events (`worktree`, `implement`, `gates`, `review`, `policy`, `integrate`, each `running`, `passed`, `failed` or `skipped`, with the attempt number; a retry starts again at `implement`); `GET /api/projects/{project}/runs/{run_id}/events?attempt=N&after=<seq>&limit=` (default 500, max 2,000, oldest first, `next_after`).
- Opening the Run tab mid-run loads the current attempt's events from its start, then subscribes from the last `seq` loaded; events are kept per attempt, deduplicated and in `seq` order; a new attempt switches the view.
- Header: ticket chip and title (opens the drawer), "Attempt 2 of 4", backend, elapsed time, usage; the step indicator Worktree → Implement → Gates → Review → Policy → Integrate with icon + label.
- Transcript (60%): agent messages as safe Markdown; tool calls as collapsed rows (tool, file or command, duration) that expand to at most 200 lines of plain text; denied commands as a red row; file edits with line counts; stream warnings and usage-limit pauses as muted rows; nothing clickable or rendered as HTML; auto-scroll with "Jump to latest"; the last 500 rows with **Show earlier**.
- Right panel (40%): the Gates, Review and Diff labels with "Details come in T39".
- Result panel at the end of a run: merged (with the next ticket), blocked (**Unblock**), needs approval (**Review**), paused by a usage limit, cancelled or interrupted (**Run next**).
- No active run: no runs yet, the last run's summary with **Run next**, a finished `?attempt=N` with **Show current run**, loading and error states.

Done when:

- [ ] A full fake run plays live with no reload
- [ ] Opening the Run tab mid-run shows the attempt from its start, with no gaps or duplicates
- [ ] The result panel names the outcome and its next action

### T39 · Run details

See why an attempt passed or failed. *Depends on: T22 · 2 h*

- The right-hand sub-tabs: **Gates** (each command with pass/fail and duration, trimmed output with the first failure highlighted), **Review** (each "Done when" item met or not met with the reviewer's reason, and the verdict) and **Diff** (file list with change counts, unified diff).
- File-edit rows in the transcript expand to a mini diff.
- The drawer's gate and reviewer lines.

Done when:

- [ ] A failed gate shows its command, duration and first failure line
- [ ] The review panel shows every "Done when" item with its verdict and reason
- [ ] The diff panel shows each changed file with a unified diff

### T40 · Past runs and replay

Look back at any earlier attempt. *Depends on: T39 · 2 h*

- The **Past runs** table (ticket, attempt, outcome, duration, usage, finished), paged.
- A row opens the run layout in replay mode with the banner "Viewing attempt 2 · finished 14:02 · Blocked" and no controls.
- `?attempt=N` for a finished attempt opens its replay; past events load only when opened.

Done when:

- [ ] A past run opens in replay with the same layout and no controls
- [ ] A drawer attempt link opens that attempt's replay

### T42 · Repo safety

Nothing in a repo can loosen SpoolHQ's limits or run code through SpoolHQ's git calls. *Depends on: T36 · 1.5 h*

- Inventory, from each adapter's current docs, of the files in the working folder it reads that can change permissions, run code or add tools (`.claude/settings.json`, `.claude/settings.local.json`, their hooks, `.mcp.json`, project Codex config), with the version checked; instruction files (`CLAUDE.md`, `AGENTS.md`) grant nothing and stay.
- Every adapter loads only SpoolHQ's per-run settings: the flag or option that limits setting sources, with project MCP servers and hooks off. An adapter that can't exclude such a file is refused before the agent starts: "This repo has agent settings SpoolHQ can't override for <backend>: <file>", with no weaker fallback; checked on the worktree at the start of every attempt.
- Files under `.claude/`, `.codex/` and `.mcp.json` written or changed by the implementer fail the attempt's policy step with "The agent changed agent settings: <file>" and block the ticket; they never reach main.
- Every hook-firing git call SpoolHQ makes (commit, merge, rebase, checkout, worktree add) runs with `-c core.hooksPath=<empty folder SpoolHQ owns>`, through an argument list, in one shared helper; the gates do the checking.
- A "Repo safety" section in `docs/agents.md`; DECISIONS entries.

Done when:

- [ ] A repo containing its own agent settings or hooks can't loosen the per-run limits (tested per adapter)
- [ ] An agent can't plant agent settings that reach main or affect the next attempt
- [ ] SpoolHQ's own git calls never run repo git hooks

### T43 · Existing repo onboarding

Make an existing repo quick to set up. *Depends on: T42 · 2.5 h*

- A read-only `POST /api/repos/inspect`: branch, clean state, GitHub origin, commands detected from a justfile, Makefile, `package.json` or `pyproject.toml`, agent settings found, missing notes files.
- The dialog pre-fills the commands and the remote, and shows notices for agent settings and Graphify.
- A failing baseline reads "Your tests fail before any change", with the output.
- `PROGRESS.md` and `DECISIONS.md` are created on the first merge only when missing; `CLAUDE.md` is never written.
- A push rejected by branch protection gives a fixed message.
- Ticket ids are never reused (also counting git tags and the run log) and are assigned under a lock shared by the CLI and the daemon.
- The starter spec counts as no spec for Run next.

Done when:

- [ ] Commands are pre-filled for a justfile, an npm and a Python fixture repo
- [ ] A failing baseline is reported as the repo's own failure
- [ ] Ticket numbers are never reused, even across the CLI and the app

### T44 · Drafting in the form

Draft tickets from a few lines in the Add ticket form. *Depends on: T41 · 2 h*

- A Describe it box and **Draft with planner** in the empty form, disabled with the daemon's reason.
- "Drafting…" with Cancel, polling the job.
- One draft fills the form; two or three drafts show as tabs D1 to D3, each the normal edit form.
- Problems next to their field and on their tab, with Save disabled until fixed.
- **Save all** through the batch route.
- Discard, a confirm when closing with drafts, and Try again on a failed job.

Done when:

- [ ] A few lines produce a draft that opens in the form, unsaved
- [ ] Two or three drafts show as tabs and save together with Save all
- [ ] A draft with problems can't be saved until fixed

### T47 · Project settings: agents

Pick each role's backend and model from the app. *Depends on: T32, T27 · 2 h*

- A fourth tab in the project panel: **Spec · Tickets · Run · Settings**. Project settings live only in this tab and are stored in that project's `project.yaml` in the workspace, never in the repo.
- In T47 the tab has one section, **Agents**: planner, implementer and reviewer, each with a backend dropdown from the detected backends ("Use default" first), an optional model name, and under **Advanced** a base URL (plain http only for localhost). Plus the default backend.
- Saves through the existing settings route with ETag; a 412 shows the "Changed on disk · Reload · Keep mine" bar; a 422 shows next to its field.
- App Settings (the existing dialog) stays app-wide only. Its gear tooltip reads "App settings", and its Agents tab line reads "Set per project in its Settings tab".
- The panel's invalid-settings bar links to the Settings tab; a project card's menu on Home gets "Project settings".
- The rest of the project settings (commands, merge policy, limits, ClickUp) join this tab in v0.2.

Done when:

- [ ] Changing a role's backend in the tab saves to `project.yaml`, and the next run uses it
- [ ] An invalid base URL is refused next to its field
- [ ] App Settings shows nothing per project

### T51 · Tracker sync in the app

Show tracker sync in the app, so a failed sync is never silent. *Depends on: T24, T33 · 1.5 h*

- Daemon: `POST …/tracker/retry` re-queues the project's failed actions and clears the failed state (200 and nothing done when none failed); the sync worker also starts when a project's settings are saved with a `tracker` block, so adding a tracker needs no restart; `last_error` is a fixed message built by code, never a response body or the token.
- Project header: only with a tracker, a sync line next to the remote, as icon + label: "ClickUp · synced 2 min ago" (absolute time on hover), "ClickUp · syncing · 3 pending", or "ClickUp · sync failed" in red with the error in the tooltip and **Retry**; a small **Push now**, disabled with a reason while syncing.
- Home: a failed sync is a Needs-you card ("ClickUp sync failed", the project, the error, the age, **Retry**) that goes away once sync is ok.
- Sync runs outside ticket runs, so the app refetches the tracker state every 15 s, only for on-screen projects with a tracker, and right after Push now or Retry.

Done when:

- [ ] Plan.md lists T51, with consistent table, totals and critical path
- [ ] The project header shows the sync state, and a failed sync shows its error with Retry
- [ ] A failed sync appears as a Needs-you card on Home
- [ ] Adding a tracker to a project's settings starts sync without a restart
- [ ] Lint and tests pass, and CI is green on Linux, macOS and Windows

### T23 · Bundled daemon

The app brings its own daemon. *Depends on: T21, T40, T36, T37, T41, T42, T43, T44, T45, T46, T47, T48, T51 · 2 h*

- The daemon is built with PyInstaller and shipped as a Tauri sidecar; the app starts it when none is running and connects to a running one otherwise.
- `devtools/` and the fake runner are left out of the build, and the packaged daemon refuses `SPOOLHQ_DEV_FAKE_RUNNER`.
- A smoke test of the built daemon (health, `spool init`) on each OS in CI.

Done when:

- [ ] The app starts the bundled daemon when none is running, and uses a running one otherwise
- [ ] The packaged daemon contains no dev tools and refuses the fake runner
- [ ] The built daemon passes its smoke test on Linux, macOS and Windows

### T49 · Background running and tray

Runs keep going when the window closes. *Depends on: T23 · 1.5 h*

- Closing the window leaves the daemon and any run going.
- A tray icon with Open and Quit.
- Quit stops the daemon and any running agent cleanly, with the run marked as cancelled, not interrupted.

Done when:

- [ ] Closing the window leaves a run going, and reopening shows it live
- [ ] Quitting from the tray stops the daemon and any running agent cleanly, with no leftover process

### T50 · Installers and update feed

Installers for every OS and a signed update feed, built by CI on release tags. *Depends on: T49 · 2.5 h*

- One version everywhere: the daemon package, `desktop/package.json` and `tauri.conf.json`; `just set-version <x.y.z>` updates all three, and the release fails with "Tag v0.1.0 doesn't match the app version 0.0.9" when they differ.
- `release.yml` on `v*` tags and on `workflow_dispatch` with a `dry_run` input: Linux AppImage, `.deb` and `.rpm`; the Windows NSIS setup `.exe`; a macOS `.dmg` for arm64 (x86_64 only if a GitHub runner for it exists). Each build makes the real sidecar for its OS first, then the Tauri bundle. No code signing yet; `docs/packaging.md` says how to open an unsigned app.
- Tauri's updater plugin, pinned exactly and used only from Rust (no webview permission); the public key in `tauri.conf.json`; the endpoint `https://github.com/ATOM43/Spoolhq/releases/latest/download/latest.json`.
- The workflow signs the update artifacts with `TAURI_SIGNING_PRIVATE_KEY` and its password from GitHub secrets ("Set the TAURI_SIGNING_PRIVATE_KEY secret; see docs/packaging.md" when missing) and builds `latest.json` (version, notes, date, each platform's URL and signature, an optional empty `minimum_version`). Linux updates go through the AppImage only.
- A tag creates a draft GitHub Release with every installer and `latest.json`; a dry run uploads workflow artifacts only.
- CI checks each bundle: the sidecar is inside, the T23 smoke test passes against it, and `latest.json` lists the platform with a signature.
- `docs/packaging.md`: installers, the feed, how to generate, store and back up the signing key, unsigned builds.

Done when:

- [ ] Plan.md lists the extended T50 and T52, with consistent table, totals and critical path
- [ ] A dry run produces installers for Linux, macOS and Windows, each with a working bundled daemon
- [ ] A tag produces a draft release with the installers and a signed `latest.json`
- [ ] A tag that doesn't match the app version fails the release
- [ ] Lint and tests pass, and CI is green on Linux, macOS and Windows
- [ ] A fresh machine with only the installer and git can create a project and run a ticket

### T52 · Update check in the app

Tell users about a new version and install it safely. *Depends on: T50 · 1.5 h*

- Check the update feed at launch and every 6 h, from Rust.
- "Update available · v0.2.0" in Home's top bar and Settings → About, with the release notes as plain text.
- **Install and restart**, disabled with a reason while a run is going.
- A setting to turn checks off; a failed check shows only a quiet line in About.
- The feed's `minimum_version` field is read but not enforced in v0.1.0.

Done when:

- [ ] A newer version in the feed shows the notice, and Install and restart updates the app
- [ ] An update never installs while a run is going
- [ ] An update with a bad signature is refused

## Phase 5 — Tracker, dogfood and release

Three tickets connect ClickUp, prove the tool on a real project, and publish v0.1.0 (milestone M2).

### T24 · Tracker adapter and ClickUp

Tickets mirrored to ClickUp; local files stay the source of truth. *Depends on: T05, T14 · 3 h*

- `TrackerAdapter` interface: `push_ticket`, `update_status`, `comment`, `link_pr`.
- ClickUp: project → list, ticket → task with the ticket id in a custom field; status mapping in `project.yaml`.
- One-way sync; the stored `tracker_ref` makes every push idempotent.
- After each run, a comment with the outcome, cost and PR link. A dry-run mode prints what would change.

Done when:

- [ ] Pushing the same plan twice creates no duplicate tasks
- [ ] A ClickUp outage marks sync as failed without stopping the run loop

### T25 · Dogfood on the dashboard task

The first real test, against a plan you already wrote by hand. *Depends on: T16, T18, T21, T40 · 3 h*

- Run the simulation-dashboard spec end to end with the fastapi-react template.
- Compare the planner's tickets with the hand-written 18-ticket plan.
- Record per ticket: passed first try, retries, review verdicts, human interventions, cost, time.
- Turn every failure into an issue; fix the blocking ones before release.

Done when:

- [ ] The dashboard app is built and its own tests pass
- [ ] Results are published in `docs/benchmarks/dashboard.md`

### T26 · Documentation and release

What a stranger needs to install it and trust it. *Depends on: T50, T52, T25 · 2.5 h*

- README: what it is, install, a first project in five minutes, screenshots.
- `docs/`: architecture, ticket format, writing a template, writing a tracker adapter, security model.
- `DECISIONS.md`: stack choices, files plus SQLite for storage, why no skip-permissions, alternatives considered (Kontora as a base, Electron, cookiecutter).
- Tag v0.1.0 with installers attached.

Done when:

- [ ] Someone else installs it and runs a template project from the README alone
- [ ] Every v1 item in the overview maps to a ticket, a test or a doc page

### T28 · Code graph with Graphify

A map of the codebase that stays current, so the agent finds the right files without re-reading the repo. *Depends on: T14, T16 · 2.5 h*

- Graphify is optional and external (tested with 0.9.92). Without it, or when it fails or passes 120 s, runs carry on without a map; `spool agents` shows whether it is found.
- In the run's worktree, before the first attempt and before a retry only if the code changed, Graphify builds or incrementally updates the graph, offline and code-only. The cache is kept once per project in `<workspace>/.spoolhq/codegraph/`, saved atomically, rebuilt when an update fails or Graphify's version changes, and locked. It is never inside the repository and never committed by SpoolHQ.
- The report's summary goes into the implementer's and planner's prompts as a "Code map" block, escaped, counted against the context budget, capped by `context.code_map_chars` (0 turns it off) and trimmed least connected first. The reviewer doesn't get it. Graphify's own hooks are never installed, and AI labels are left for later.

Done when:

- [ ] The implementer and planner get a trimmed code map when Graphify is installed
- [ ] The per-project cache is updated incrementally, saved atomically and rebuilt when broken
- [ ] Runs work unchanged when Graphify is missing, fails or times out
- [ ] Nothing from the graph is committed by SpoolHQ

## Later phases

Not estimated yet; each gets its own ticket plan after v0.1.0. The v1 interfaces are designed so these slot in without rewrites.

| Phase | What it adds | Builds on |
| --- | --- | --- |
| 6 Docker execution | The agent runs in a container with the worktree bind-mounted, so code changes stay on your machine; network allowlist; secrets from an env file, not the command line | AgentRunner (T09) |
| 7 Parallel agents | Several independent ready tickets at once; a merge queue integrates one at a time; a conflict re-runs the ticket on the new main | Scheduler (T06), integration (T14) |
| 8 Trackers | Two-way ClickUp sync, a Jira adapter, and webhook intake so a new tracker task can start a run | TrackerAdapter (T24) |
| 9 More agents | Aider and other coding agents behind the same runner interface; Antigravity CLI (replaces Gemini CLI, closed source; check its headless mode and sandbox first) | AgentRunner (T09) |
| 10 Template registry | A shared index of community templates, versioned and contract-checked | Template library (T16) |
| 11 Full desktop UI | The 16-screen design in screens-prompt.md: Inbox, Overview, History, plan graph, Templates and Settings screens, global run bar | v0 screens (T20–T22) |

## Definition of done, risks and open questions

**Every ticket, before merge**

- [ ] Its "Done when" boxes are all ticked
- [ ] New logic has tests; `just test` is green in CI
- [ ] Lint and format pass
- [ ] The pull request lists what changed and any decision worth adding to `DECISIONS.md`

**Risks and fallbacks**

| Risk | Effect | Fallback |
| --- | --- | --- |
| The agent loops on a ticket it cannot solve | Cost rises, nothing merges | Per-ticket budget and retry limits in `project.yaml`; blocked when they run out |
| The agent runs a harmful command before Docker exists | Damage outside the worktree | Command allowlist and path hook (T09); Docker in Phase 6 |
| Planner tickets are too large or vague | The implementer fails repeatedly | Size rules in the planner prompt; the approval gate (T21); split tickets from the board |
| The PyInstaller sidecar breaks on one OS | T23 overruns | Ship the daemon as a pip package with `orch serve` and let the app connect to it |
| The Kontora spike shows Phase 2 already exists | Duplicate work | Build on Kontora; contribute the planner, templates, merge policy and UI |
| Running short of time | The release slips | Cut in this order: past-runs list in the Run tab, the tray icon (T49; closing the window then quits the daemon), Windows build. Never cut gates, the reviewer, the merge policy or crash recovery |

**Open questions**

- Should tickets live in the workspace folder (no commit noise) or inside the repo under `.orch/` (they travel with the code)? The plan assumes the workspace.
- Default merge policy: merge directly unless a rule triggers, or open a PR unless the ticket is marked trivial?
- Should the reviewer use a different model from the implementer, to reduce shared blind spots?
- Project and CLI name before the first public commit; `orch` is a placeholder.
- Licence: Apache-2.0 is assumed. AGPL would keep forks open but slows adoption.

## Sources

Tool pages checked on 17 Oct 2026: [Kontora](https://pkg.go.dev/github.com/worksonmyai/kontora@v0.13.0), [Task Master](https://github.com/codeinout22/claude-task-master), [OpenAI Symphony](https://www.heyuan110.com/posts/ai/2026-03-05-openai-symphony-autonomous-coding/), [Vibe Kanban](https://github.com/BloopAI/vibe-kanban), [Vibe Kanban shutdown notice](https://vibekanban.com/blog/shutdown), [Claude Squad](https://claudeskills.info/harness/claude-squad/).
