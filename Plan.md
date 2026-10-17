# Agent Orchestrator — Ticket Plan

Oct 17, 2026 · @Atom

## Overview

The app turns a written task spec into an approved ticket plan, then has one coding agent implement the tickets in dependency order. Each ticket reaches main only after tests and an independent review pass. v1 is **26 tickets in 6 phases, about 68 hours** for one developer.

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
- **Agent runtime**: Claude Agent SDK behind an `AgentRunner` interface, so other coding agents can plug in later.

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
| T09 | Agent runner | 2 Run loop | T02 | 3 |
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
| T20 | Home, project panel and dialogs | 4 Desktop UI | T03, T19 | 3 |
| T21 | Tickets tab and drawer | 4 Desktop UI | T15, T20 | 3 |
| T22 | Run tab | 4 Desktop UI | T20 | 3 |
| T23 | Packaging | 4 Desktop UI | T21, T22 | 3 |
| T24 | Tracker adapter and ClickUp | 5 Release | T05, T14 | 3 |
| T25 | Dogfood on the dashboard task | 5 Release | T16, T18, T21, T22 | 3 |
| T26 | Documentation and release | 5 Release | T23, T25 | 2.5 |
|  | **Total** |  |  | **67.5** |

Critical path, if tickets ran in parallel: T01 → T02 → T04 → T05 → T06 → T13 → T19 → T20 → T22 → T23 → T26 (27.5 h).

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

### T09 · Agent runner

One interface for running a coding agent, with the Claude Agent SDK behind it. *Depends on: T02 · 3 h*

- `AgentRunner.run(prompt, cwd, tools, max_turns, budget_usd)` streams events and returns a summary, files changed and cost.
- The working directory is the worktree; file tools refuse paths outside it.
- No blanket skip-permissions: shell commands come from an allowlist (the stack commands plus read-only git), and a hook denies the rest.
- Timeout and cancel. A fake runner replays recorded transcripts for tests.

Done when:

- [ ] A real run creates a file in a scratch repo; the same run passes in CI with the fake runner
- [ ] A command outside the allowlist is denied and logged

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

### T13 · Run loop

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

Four tickets add the parts around the loop: turning a spec into tickets, starting projects from templates, and delivering through GitHub. From here the orchestrator implements its own tickets while you review.

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

## Phase 4 — Desktop UI (v0 screens)

Five tickets put a minimal face on the daemon and package it: two screens (Home and the project panel), a ticket drawer and three dialogs, as specified in `screens-prompt-v0.md`. The full 16-screen design in `screens-prompt.md` is the v0.2 target. Everything here already works from the CLI.

### T19 · Live API

What the app reads, and a live stream of what the agent is doing. *Depends on: T07, T13 · 2.5 h*

- REST endpoints for projects, tickets, runs and settings; a WebSocket stream of run events.
- A TypeScript client generated from the OpenAPI schema.
- Paged run history; ETags so a ticket edited in a file and in the app at once is never overwritten silently.

Done when:

- [ ] API tests for every endpoint, including a conflicting edit
- [ ] A test client receives every event of a fake run, in order

### T20 · Home, project panel and dialogs

The two screens and the setup dialogs. *Depends on: T03, T19 · 3 h*

- Home: project list with progress and status, a "Needs you" section, and an empty state that opens New project.
- New project dialog: name, repo path or template, the three stack commands with **Test**.
- Settings dialog: Anthropic key, GitHub and ClickUp tokens, stored in the keychain. Opens on first run when no key is set.
- Project panel shell: header with progress line and run controls that change with state (disabled controls say why); tabs Spec, Tickets, Run.
- Spec tab: markdown editor with autosave and **Generate plan**.
- A daemon-not-running state on both screens instead of a blank window.

Done when:

- [ ] From a fresh install: set the key, create a project, write a spec and generate a plan without touching the CLI
- [ ] Every disabled control shows why and what to do

### T21 · Tickets tab and drawer

Plan review, the board and approvals in one list. *Depends on: T15, T20 · 3 h*

- One list grouped by status. While the plan is a draft, a banner shows the ticket count, validation problems and **Approve plan**.
- Ticket drawer: details, "Done when" with the latest review result, dependencies, attempts. Editable when draft, ready or blocked.
- Contextual actions: **Run this ticket**, **Unblock**, **Approve and merge** or **Request changes** in local mode, the PR link in GitHub mode.
- One note-to-agent dialog, shared by Unblock and Request changes.

Done when:

- [ ] A plan with a cycle cannot be approved, and the problem links to the ticket
- [ ] Edits round-trip to the ticket files and survive a reload

### T22 · Run tab

Watch the agent and inspect past attempts. *Depends on: T20 · 3 h*

- Live transcript with collapsible tool calls; sub-tabs Gates, Review and Diff.
- Step indicator (Worktree → Implement → Gates → Review → Policy → Integrate), attempt number, elapsed time, cost.
- A result panel at the end of each run with the next action: view the next ticket, unblock, or review.
- With nothing running: **Run next** and a list of past runs that open in replay.

Done when:

- [ ] A full fake run plays live with no reload
- [ ] Unblocking with a note starts an attempt whose prompt contains the note

### T23 · Packaging

One installer that brings its own daemon. *Depends on: T21, T22 · 3 h*

- The daemon is bundled with PyInstaller and shipped as a Tauri sidecar; the app starts it when it is not running.
- Closing the window leaves the daemon and any run going, with a tray icon to quit.
- CI builds installers for macOS, Windows and Linux.

Done when:

- [ ] A fresh machine with only the installer and git can create a project and run a ticket
- [ ] Quitting from the tray stops the daemon and any running agent cleanly

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

The first real test, against a plan you already wrote by hand. *Depends on: T16, T18, T21, T22 · 3 h*

- Run the simulation-dashboard spec end to end with the fastapi-react template.
- Compare the planner's tickets with the hand-written 18-ticket plan.
- Record per ticket: passed first try, retries, review verdicts, human interventions, cost, time.
- Turn every failure into an issue; fix the blocking ones before release.

Done when:

- [ ] The dashboard app is built and its own tests pass
- [ ] Results are published in `docs/benchmarks/dashboard.md`

### T26 · Documentation and release

What a stranger needs to install it and trust it. *Depends on: T23, T25 · 2.5 h*

- README: what it is, install, a first project in five minutes, screenshots.
- `docs/`: architecture, ticket format, writing a template, writing a tracker adapter, security model.
- `DECISIONS.md`: stack choices, files plus SQLite for storage, why no skip-permissions, alternatives considered (Kontora as a base, Electron, cookiecutter).
- Tag v0.1.0 with installers attached.

Done when:

- [ ] Someone else installs it and runs a template project from the README alone
- [ ] Every v1 item in the overview maps to a ticket, a test or a doc page

## Later phases

Not estimated yet; each gets its own ticket plan after v0.1.0. The v1 interfaces are designed so these slot in without rewrites.

| Phase | What it adds | Builds on |
| --- | --- | --- |
| 6 Docker execution | The agent runs in a container with the worktree bind-mounted, so code changes stay on your machine; network allowlist; secrets from an env file, not the command line | AgentRunner (T09) |
| 7 Parallel agents | Several independent ready tickets at once; a merge queue integrates one at a time; a conflict re-runs the ticket on the new main | Scheduler (T06), integration (T14) |
| 8 Trackers | Two-way ClickUp sync, a Jira adapter, and webhook intake so a new tracker task can start a run | TrackerAdapter (T24) |
| 9 More agents | Other coding agents (Codex CLI, Aider) behind the same runner interface | AgentRunner (T09) |
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
| Running short of time | The release slips | Cut in this order: past-runs list in the Run tab, tray icon, Windows build. Never cut gates, the reviewer, the merge policy or crash recovery |

**Open questions**

- Should tickets live in the workspace folder (no commit noise) or inside the repo under `.orch/` (they travel with the code)? The plan assumes the workspace.
- Default merge policy: merge directly unless a rule triggers, or open a PR unless the ticket is marked trivial?
- Should the reviewer use a different model from the implementer, to reduce shared blind spots?
- Project and CLI name before the first public commit; `orch` is a placeholder.
- Licence: Apache-2.0 is assumed. AGPL would keep forks open but slows adoption.

## Sources

Tool pages checked on 17 Oct 2026: [Kontora](https://pkg.go.dev/github.com/worksonmyai/kontora@v0.13.0), [Task Master](https://github.com/codeinout22/claude-task-master), [OpenAI Symphony](https://www.heyuan110.com/posts/ai/2026-03-05-openai-symphony-autonomous-coding/), [Vibe Kanban](https://github.com/BloopAI/vibe-kanban), [Vibe Kanban shutdown notice](https://vibekanban.com/blog/shutdown), [Claude Squad](https://claudeskills.info/harness/claude-squad/).
