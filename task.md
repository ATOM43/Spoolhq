# SpoolHQ — Task

Name: SpoolHQ (package `spoolhq`, CLI `spool`).
Status: building. Ticket plan: "Agent Orchestrator — Ticket Plan" (27 tickets, 6 phases, ~71 h).

This file is the root context for the project. It states what to build and why. The ticket plan states the order to build it in. Once SpoolHQ reaches milestone M1, this file becomes the `CONTEXT.md` it reads while implementing its own remaining tickets.

## Objective

Build an open-source, local-first desktop app that turns a written task spec into a reviewed ticket plan, then has a coding agent implement those tickets one by one, in dependency order. Each ticket reaches the main branch only after automated checks and an independent review pass.

The goal is to stop repeating the same manual cycle for every new project: asking an AI to break down the work, scaffolding the same stack, prompting ticket by ticket, checking the result and merging by hand. SpoolHQ should make that cycle structured, repeatable and traceable in git.

It must work for people who pay for a coding-agent subscription (Claude, ChatGPT, Google) but have no API key, by driving the coding CLI they already have installed.

## Background

Coding agents such as Claude Code, Codex CLI and Gemini CLI can implement a well-scoped ticket on their own. What is still manual is everything around that:

- Splitting a large task into small, ordered tickets with clear acceptance criteria.
- Setting up the same project structure and tooling for each new stack.
- Giving each ticket's agent the right context about what already exists.
- Checking the work, reviewing it, and merging it without breaking main.
- Keeping a tracker such as ClickUp in step with what actually happened.

Existing open-source tools cover parts of this (Kontora, Task Master, OpenAI Symphony, Vibe Kanban, Claude Squad). None combines spec-to-plan, reusable stack templates, an autonomous dependency-ordered loop with a merge policy, and tracker sync. See the Prior art section of the ticket plan.

## Core concepts

| Concept | Meaning |
| --- | --- |
| Project | A folder holding one spec, its settings, its tickets and its run history, linked to one git repo. Similar to a Claude Project. |
| Spec | `CONTEXT.md`: the full task description, like this file. |
| Ticket | One unit of work: scope, dependencies, estimate, "Done when" checklist. One ticket = one branch = one merge. |
| Plan | The set of tickets for a project. Drafted by the planner agent, approved by a human. |
| Run | One attempt to take a ticket from ready to merged. A ticket can have several attempts. |
| Gate | A deterministic check (install, lint, test) run by code, not by an agent. |
| Template | A reusable project skeleton (Copier) that also defines the commands gates run. |
| Merge policy | Rules deciding whether a ticket merges directly or waits for human approval via a pull request. |
| Agent backend | The coding agent that does the work: an installed CLI (Claude Code, Codex, Gemini) using the user's own login, or the Claude Agent SDK with an API key. |

## User workflow

A user should be able to:

1. Create a project, either from a template (for example FastAPI + React) or from an existing repo.
2. Pick an agent backend: a coding CLI they are logged into, or an API key.
3. Write or paste the spec into `CONTEXT.md`.
4. Ask the planner to draft tickets, then review, edit, split or merge them, and approve the plan.
5. Start the run: the agent works through ready tickets one at a time.
6. Watch progress live: transcript, check results, review verdict, diff, usage or cost.
7. Approve pull requests for tickets the merge policy flags; unblock tickets the agent could not finish, with a note.
8. See tickets mirrored in ClickUp, with status and a comment per run.
9. Come back later and follow the full history: which run produced which commit, why it was merged, what it used.

## Agents and their roles

Only three roles are LLM agents. Everything else is plain, testable code. Each role can use a different agent backend.

| Role | Type | Input | Output |
| --- | --- | --- | --- |
| Planner | Agent | Spec, template description | Draft tickets (schema-validated) |
| Implementer | Agent | Ticket, spec excerpt, `PROGRESS.md`, `DECISIONS.md`, `CLAUDE.md`, last failures | Code changes in a worktree, a progress note |
| Reviewer | Agent, fresh context, read-only | Ticket, diff, gate results (never the implementer's transcript) | Verdict per "Done when" item: met / not met, plus approve, changes_requested or needs_human |
| Gates | Code | Worktree, stack commands | Pass/fail per command with trimmed output |
| Scheduler | Code | Ticket graph, statuses | Next ready ticket |
| Integrator | Code | Approved attempt | Commit, rebase, re-check, squash-merge, tag, push |
| Tracker sync | Code | Ticket changes, run results | ClickUp tasks and comments |

## Run loop (one ticket)

1. Pick the lowest-numbered ticket whose dependencies are all done.
2. Create a git worktree and branch (`feat/T04-<slug>`) from the latest main.
3. Implementer works on the ticket.
4. Gates run. On failure, the errors go back to the implementer (up to 3 retries).
5. Reviewer checks the diff against the ticket. On changes requested, the notes go back to the implementer (up to 2 retries).
6. Retry limits used up, or reviewer says needs_human: the ticket is **blocked** and waits for the user. A subscription usage limit is different: the run **pauses** until the reset time, and the ticket is not blocked.
7. Merge policy decides:
   - Direct: rebase onto main, re-run gates, squash-merge, tag `ticket/T04`, push main if GitHub is configured.
   - Review required: push the branch, open a pull request, wait. Merged → pull main. Changes requested → new attempt with the PR comments.
8. Mark the ticket done, append its progress note to `PROGRESS.md`, update the tracker, continue with the next ticket.

## Requirements

### Projects and tickets

- Projects are folders; tickets are markdown files with YAML frontmatter. Files are the source of truth, so they stay readable, diffable and usable by agents without an API.
- Run history, events and usage are stored in SQLite inside the project workspace.
- Ticket statuses: draft, ready, running, awaiting_approval, blocked, done. Only defined transitions are allowed.
- The dependency graph is validated: unknown dependencies, cycles and duplicate ids are rejected with a named error.
- Reading and writing a ticket file must not reorder or lose content the user wrote.

### Planning

- The planner produces tickets of 1.5 to 4 hours, each with scope, dependencies, estimate, "Done when" and a `review_required` flag.
- Planner output is validated against the ticket schema and graph rules before it is written.
- Nothing runs until the user approves the plan. Re-planning keeps tickets the user edited.

### Templates

- Templates are Copier projects, from a local folder or a git URL, so generated projects can be updated when a template improves.
- Every template must declare its `install`, `test` and `lint` commands, and they must pass on a freshly generated project. This is the contract gates rely on.
- First template: FastAPI + SQLAlchemy + pytest backend, React + Vite + TypeScript frontend, `justfile`, `CLAUDE.md` with conventions, CI.
- Applying a template is done by code, not by an agent; plans start at real work.

### Agent backends

- One `AgentRunner` interface; each backend is an adapter that streams normalised events (message, tool call, file edit, usage) and returns a summary, files changed and usage.
- Backends: Claude Code CLI (default, first), Codex CLI, Gemini CLI — each driven headless with JSON output, using the user's own installed CLI and login — and the Claude Agent SDK for users with an API key.
- Each adapter translates SpoolHQ's policy (worktree-only file access, shell allowlist) into that CLI's own permission or sandbox settings. A backend that cannot enforce the policy is refused.
- Subscription backends report tokens and usage limits; API backends report cost. Budgets apply to whichever the backend reports.
- `spool agents` and the Settings dialog list detected backends, versions and login status. The backend is chosen per project and per role.
- Before release, each vendor's terms for driving its CLI from a third-party tool with a subscription login are checked and recorded in `DECISIONS.md`.

### Execution and git

- v1 runs one agent at a time, directly on the user's machine, inside a git worktree.
- SpoolHQ, not the agent, makes commits and merges.
- Local git always works without any remote.
- If a GitHub remote is configured: direct-mode tickets push to main; review-required tickets open a pull request.
- A ticket goes through a PR when any rule holds: `review_required` is set; the diff exceeds a configured size; protected paths are touched (for example migrations, CI, auth); the reviewer says needs_human. Without a remote, the same rules pause for approval in the app.
- main must never be left in a broken or mid-rebase state, even if the daemon is killed.

### Tracker

- A `TrackerAdapter` interface (`push_ticket`, `update_status`, `comment`, `link_pr`).
- First adapter: ClickUp, one-way (local → ClickUp), idempotent via a stored `tracker_ref`.
- A tracker outage must not stop the run loop.

### Application

- **Daemon** (Python, FastAPI): owns projects, the run loop, git and the tracker. Keeps running when the window is closed; can run headless on a server.
- **CLI** (`spool`, Typer): every action is available without the UI.
- **Desktop app** (Tauri 2, React, TypeScript): Home, project panel (Spec · Tickets · Run), ticket drawer, settings. It talks only to the daemon's API.
- Installers for macOS, Windows and Linux, with the daemon bundled as a sidecar.

### Security

- The daemon listens on 127.0.0.1 only and requires a local token.
- No blanket `--dangerously-skip-permissions` or equivalent on any backend: file access is confined to the worktree, and shell commands come from an allowlist (the stack commands plus read-only git); everything else is denied and logged.
- All git and process calls use argument lists, never a shell string. Ticket text and tracker content are untrusted input.
- Secrets (API keys, GitHub and ClickUp tokens) come from the OS keychain or environment variables, never from files in the workspace or command-line arguments. CLI logins stay in each CLI's own store; SpoolHQ never reads or copies them.
- Per-ticket budget and retry limits prevent runaway cost or usage.

### Reliability and quality

- Every run, attempt and event is recorded; a crash marks running work as interrupted, and stale worktrees are cleaned on startup.
- Gates are deterministic: the same input gives the same result.
- Core logic (ticket store, scheduler, gates, run loop, integration, merge policy) is tested with a fake agent runner that replays recorded transcripts, so CI never calls a real model. Every backend adapter passes one shared contract test suite.

## File layout

Project workspace (outside the repo):

```text
~/spoolhq-projects/<project>/
  project.yaml        # settings: repo, branch, stack commands, agent backends, limits, merge policy, remote, tracker
  CONTEXT.md          # the spec
  tickets/
    T01-repo-tooling.md
    T02-daemon-scaffold.md
  runs/<ticket>/<attempt>/   # transcript, gate output, diff, review verdict
  .spoolhq/state.db   # runs, attempts, events, usage
```

In the code repo, because agents read them with the code:

```text
PROGRESS.md    # what each merged ticket added; the handoff between tickets
DECISIONS.md   # decisions and their reasons
CLAUDE.md      # conventions from the template
```

Example ticket file:

```markdown
---
id: T04
title: Project workspace and settings
phase: 1
depends_on: [T02]
status: ready
estimate_h: 2
review_required: false
tracker_ref: null
---

## Scope
- `spool init <name> --repo <path>` creates the workspace folder.
- `project.yaml` validated by Pydantic; errors name the field.

## Done when
- [ ] `spool init` on an existing repo creates a valid workspace
- [ ] `just test` passes
```

Example `project.yaml`:

```yaml
name: sim-dashboard
repo: ~/code/sim-dashboard
default_branch: main
template: fastapi-react
commands:
  install: just install
  lint: just lint
  test: just test
agents:
  default: claude-code-cli        # claude-code-cli | codex-cli | gemini-cli | claude-agent-sdk
  reviewer: codex-cli             # optional per-role override
  budget_per_ticket:
    usd: 5                        # API backends
    tokens: 2000000               # subscription backends
limits:
  gate_retries: 3
  review_retries: 2
merge_policy:
  max_diff_lines: 400
  protected_paths: ["**/migrations/**", ".github/**", "**/auth/**"]
git:
  remote: https://github.com/<owner>/<repo>   # optional
tracker:
  kind: clickup                               # optional
  list_id: "<list id>"
```

## Out of scope for v1

Planned as later phases, with v1 interfaces designed so they slot in:

- Docker execution, with the worktree bind-mounted so code changes stay on the host.
- Several agents working on independent tickets in parallel, with a merge queue.
- Two-way tracker sync, a Jira adapter, webhook intake.
- Further agent backends (Aider and others).
- A shared template registry.
- Multi-user accounts, hosted service, authentication beyond the local token.

## Deliverables

- Public GitHub repository under Apache-2.0 with daemon, CLI, desktop app and the first template.
- Installers for macOS, Windows and Linux (v0.1.0 release).
- Tests for the ticket store, scheduler, gates, run loop, integration, merge policy and backend adapters, green in CI on all three operating systems.
- `README.md`: install, first project in five minutes, screenshots.
- `docs/`: architecture, ticket format, agent backends, writing a template, writing a tracker adapter, security model.
- `DECISIONS.md`: assumptions, stack choices, alternatives considered, open questions.
- `docs/benchmarks/dashboard.md`: results of the dogfood run.

## Success criteria

- **M1 — self-hosting (after T14):** SpoolHQ implements and merges at least one real ticket in its own repo from the CLI, using a subscription login through the Claude Code CLI.
- **Dogfood (T25):** the simulation-dashboard task is built end to end from its spec with the fastapi-react template, and the resulting app's tests pass. Recorded per ticket: passed first try, retries, review verdicts, human interventions, usage, time. The planner's tickets are compared with the hand-written 18-ticket plan.
- **M2 — v0.1.0 (after T26):** someone other than the author installs the app and runs a template project using only the README.

## Decisions so far

- Name: SpoolHQ; package `spoolhq`, CLI `spool`, repo `spoolhq`.
- Desktop shell: Tauri 2 with a React + TypeScript frontend.
- Backend: a Python daemon (FastAPI) separate from the UI, so runs survive closing the window and the same code runs headless.
- Agent backends: an `AgentRunner` interface with adapters for installed coding CLIs (Claude Code first, then Codex and Gemini) so a subscription is enough, plus the Claude Agent SDK for API keys.
- Templates: Copier rather than cookiecutter, because it can update generated projects.
- Storage: files for projects and tickets, SQLite for run history.
- Execution: directly on the machine first, Docker later.
- Git: local first; GitHub direct push for simple tickets, pull requests for review-required ones.
- Tracker: ClickUp first (simpler API than Jira), one-way.
- Order: CLI and run loop before UI, so SpoolHQ can build itself from Phase 3.
- Review: binary verdict per acceptance criterion, not a numeric score.

## Open questions

- Should tickets live in the workspace (no commit noise) or in the repo under `.spoolhq/` (they travel with the code)? Current assumption: workspace.
- Default merge policy: merge directly unless a rule triggers, or open a PR unless a ticket is marked trivial?
- Default reviewer backend: same as the implementer, or a different model by default to reduce shared blind spots?
- Do each vendor's terms allow driving its CLI from a third-party tool with a subscription login? To check before release.
- Licence: Apache-2.0 assumed; AGPL would keep forks open but may slow adoption.
