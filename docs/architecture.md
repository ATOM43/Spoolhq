# Architecture

SpoolHQ has two code bases: the Python daemon (`daemon/`, package `spoolhq`), which does the work, and the desktop app (`desktop/`), a Tauri shell around a React UI that talks to the daemon over HTTP on 127.0.0.1. Both have a fixed layout with import rules that `just lint` enforces, so a misplaced import fails CI instead of slipping through review.

## Backend: `daemon/src/spoolhq/`

```text
spoolhq/
  __init__.py   # __version__
  __main__.py   # python -m spoolhq
  core/         # config, auth (token), logs — shared by everything
  api/
    app.py          # create_app, middleware wiring
    security.py     # Host check + token middleware
    routers/        # one file per resource: health.py, version.py, ...
    schemas/        # Pydantic request/response models
  services/     # domain logic, one package per domain:
                # projects, tickets, scheduler, runs, git, agents, gates, tracker
  cli/          # Typer commands (main.py) + API client (client.py)
```

### Layer rules

```text
cli    api        thin entry points: validate input, call a service, return the result
   \   /
 services         domain logic; no FastAPI, Starlette, Typer or uvicorn
    |
  core            settings, token, logging; imports nothing above it
```

- `api/` and `cli/` are thin: validate input, call a service, return the result. `cli` may import `api` (to serve it); `api` never imports `cli`.
- `services/` never import FastAPI, Starlette or Typer (or uvicorn), and never import `api` or `cli`.
- `core/` imports nothing from `api/`, `cli/` or `services/`.

[import-linter](https://import-linter.readthedocs.io/) checks these as contracts in `daemon/pyproject.toml` (`[tool.importlinter]`); `just lint` runs `lint-imports`.

### Where new backend code goes

| You are adding… | Put it in |
| --- | --- |
| A new HTTP endpoint | `api/routers/<resource>.py`, included in `api/app.py`; its models in `api/schemas/<resource>.py` |
| The logic behind it | `services/<domain>/` — the router only calls it |
| A new `spool` command | `cli/main.py` (or a module under `cli/`), calling a service or the API client |
| A setting, path or other shared helper | `core/` |
| A new domain | a new package under `services/` with a docstring saying what it owns |

New routes are token-protected by default (`api/security.py`); add a route to `PUBLIC_ROUTES` only if it must work without the token.

## Projects

A project is one workspace folder plus the git repository it works on. Workspaces live in `~/spoolhq-projects/` (the `projects_dir` setting: `config.toml` or `SPOOLHQ_PROJECTS_DIR`), one folder per project, named after the project's slug:

```text
~/spoolhq-projects/<name>/
  project.yaml   # settings: repo, branch, stack commands, agents, limits, merge policy, remote, tracker
  CONTEXT.md     # the spec the planner reads
  tickets/       # one markdown file per ticket: <id>-<slug>.md
  runs/          # one folder per attempt: runs/<ticket>/<NNN>/ (transcript, gates, diff, review)
  .spoolhq/
    state.db     # run log: runs, attempts, append-only events (SQLite)
```

`spool init <name> --repo <path>` creates it; `spool project validate <name>` checks it. The `project.yaml` format and its error messages are in [project-yaml.md](project-yaml.md).

**Code-facing notes live in the repository, not the workspace.** `PROGRESS.md`, `DECISIONS.md` and `CLAUDE.md` sit next to the code because agents read them with the code, and they travel with the repo. `spool init` never writes into the repository; it only says which of these files are missing.

The code is `services/projects/` (the model in `model.py`, YAML handling in `yaml_io.py`, the workspace in `workspace.py`), with read-only repository checks in `services/git/`. Nothing outside `services/projects/` reads or writes YAML: callers use `load_project`, `save_project` and `init_project`. Because these are local file operations, the `spool init` and `spool project validate` commands call the service directly instead of going through the daemon.

## Tickets

Each ticket is a markdown file in the workspace's `tickets/` folder: YAML frontmatter (id, title, phase, dependencies, status, estimate, ...) and a free-form body with a `## Done when` checklist. The format, its error messages and the round-trip guarantee are in [ticket-format.md](ticket-format.md).

The code is `services/tickets/`: the frontmatter model in `model.py`, splitting and changed-keys-only frontmatter updates in `document.py`, the Done-when parser in `checklist.py`, `list_tickets` / `load_ticket` / `save_ticket` in `store.py` and the editor session in `editor.py`. It reuses `format_errors` and `write_atomic` from `services/projects/`. `spool tickets list|show|edit` (in `cli/tickets.py`) call the service directly, like the project commands.

## Scheduler

The scheduler works on the plan as a whole: it checks the dependency graph (unknown dependencies, cycles, duplicate ids), owns the table of allowed status changes, picks the ticket that runs next and explains why none can, and computes remaining hours and the critical path. The rules are in [scheduler.md](scheduler.md).

The code is `services/scheduler/`: plan validation in `graph.py`, `next_ready` / `explain_idle` / `waiting_on` in `schedule.py`, the transition table and `apply_transition` in `transitions.py`, and the progress figures in `progress.py`. It is pure logic over a list of tickets; only `apply_transition` touches files, through the tickets store. `spool plan check|next|summary` (in `cli/plan.py`) and `spool tickets set-status` call it directly.

## Runs

The run log records every run (one execution of the loop for one ticket), every attempt inside it (one implementer pass with its gates and review) and an append-only stream of events, in the workspace's `.spoolhq/state.db`; each attempt's files sit in `runs/<ticket>/<NNN>/`. An in-process event bus per workspace fans committed events out to subscribers (the WebSocket in T19), and at startup the daemon marks runs a stopped daemon left active as `interrupted`. The rules, the schema and the bus's lag-and-resync contract are in [runs.md](runs.md).

The code is `services/runs/`: the SQLite connection and migrations in `db.py`, `RunLog` in `log.py`, statuses and records in `model.py`, attempt files in `files.py`, `EventBus` in `bus.py`, `recover_interrupted` in `recovery.py`, and `RunRegistry` (one `RunLog` and `EventBus` per workspace) in `registry.py`. The API's lifespan (`api/app.py`) opens the registry, which runs recovery, and closes it on shutdown; `spool serve` first takes the single-instance lock in `core/daemon_lock.py`, so recovery never runs beside another live daemon. `spool runs list|show` (in `cli/runs.py`) read `state.db` directly and read-only, like the other local commands.

## Frontend: `desktop/src/` (Feature-Sliced Design)

```text
src/
  app/        # entry (main.tsx), providers (TanStack Query), router, global styles
  pages/      # one slice per route: home/, project-panel/
  widgets/    # self-contained screen blocks: top-bar/, daemon-down-panel/
  features/   # user actions and behaviours: daemon-status/ (polling + retry), open-settings/
  entities/   # domain models: daemon/; project/, ticket/, run/ (empty for now)
  shared/     # no domain knowledge: api/ (typed client), ui/ (Button, Card, Tabs, ...),
              # lib/, config/, styles/ (design tokens)
```

Inside a slice, code is grouped by segment: `ui/` for components, `model/` for state and logic, and `index.ts` for the slice's public API. `shared/` has segments only (`shared/api`, `shared/ui`, …), each with its own `index.ts`.

### Layer rules

- **Public API only.** Each slice (and each `shared/` segment) exports what others may use from its `index.ts`. Nothing imports a slice's internals (`@/features/daemon-status/model/...` is an error).
- **Downward only.** A layer imports only from layers below it: app → pages → widgets → features → entities → shared.
- **No sideways imports.** Slices on the same layer never import each other (`features/open-settings` cannot import `features/daemon-status`). If two slices need the same thing, move it down a layer.
- **Imports use the `@/` alias** across slices (`@/shared/ui`); relative paths only inside a slice.
- **Tests sit next to the code they test** (`status.ts` and `status.test.ts`).

[eslint-plugin-boundaries](https://www.npmjs.com/package/eslint-plugin-boundaries) checks these rules (`desktop/eslint.config.js`); `just lint` runs ESLint.

### Where new frontend code goes

| You are adding… | Put it in |
| --- | --- |
| A new screen / route | `pages/<name>/`, registered in `app/router/routes.tsx` |
| A block reused across pages, or a large part of one page | `widgets/<name>/` |
| Something the user does (a button with its logic, a form, polling) | `features/<name>/` |
| Types and logic for a domain object (project, ticket, run) | `entities/<name>/` |
| A daemon endpoint call | `shared/api/` |
| A generic component (no domain knowledge) | `shared/ui/` |
| A constant or helper used everywhere | `shared/config/` or `shared/lib/` |
| A provider or global setup | `app/` |

The Rust side of the desktop app (`desktop/src-tauri/`) is small and not layered: `daemon.rs` holds the only HTTP the app does.
