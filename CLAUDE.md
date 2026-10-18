# Working in this repository

Conventions for coding agents (and humans) changing SpoolHQ.

- **Before finishing, run `just lint && just test`** and fix every failure. Do not skip or disable checks to make them pass.
- **Never use `shell=True` or build shell commands from strings.** Call subprocesses with an argument list (`subprocess.run(["git", "status"])`). ruff's `S` rules enforce this in Python.
- **Never commit secrets**: no API keys, tokens, `.env` files or personal paths.
- **Keep changes inside the ticket's scope.** If you find something else that needs doing, note it in your report instead of doing it.
- **Work directly on main. No branches, no pull requests.** See `CONTRIBUTING.md`.
- Record notable choices in `DECISIONS.md` and add a `PROGRESS.md` entry for each finished ticket.

## Layout

- `daemon/` — Python package `spoolhq` (uv, src layout, Python 3.12+).
- `desktop/` — TypeScript package `@spoolhq/desktop` (pnpm, Node 24 LTS).
- `templates/` — Copier stack templates.
- `docs/` — documentation.

## Code structure

Full description and where new code goes: [docs/architecture.md](docs/architecture.md).

### Backend (`daemon/src/spoolhq/`)

```text
spoolhq/
  core/        # config, auth (token), logs — shared by everything
  api/
    app.py         # create_app, middleware wiring
    security.py    # Host check + token middleware
    routers/       # one file per resource: health.py, version.py, ...
    schemas/       # Pydantic request/response models
  services/    # domain logic, one package per domain:
               # projects, tickets, scheduler, runs, git, agents, gates, tracker
  cli/         # Typer commands + API client
```

- `api/` and `cli/` are thin: validate input, call a service, return the result.
- `services/` never import FastAPI, Starlette or Typer.
- `core/` imports nothing from `api/`, `cli/` or `services/`.
- import-linter enforces these rules (contracts in `daemon/pyproject.toml`, run by `just lint`).

### Frontend (`desktop/src/`): Feature-Sliced Design

```text
src/
  app/        # entry, providers (TanStack Query), router, global styles
  pages/      # home/, project-panel/
  widgets/    # top-bar/, daemon-down-panel/
  features/   # daemon-status/, open-settings/
  entities/   # daemon/; project/, ticket/, run/ (empty for now)
  shared/     # api/, ui/, lib/, config/, styles/
```

- Each slice exposes its public API through `index.ts`; nothing imports a slice's internals.
- A layer imports only from layers below it (app → pages → widgets → features → entities → shared); slices on the same layer never import each other.
- Import across slices with the `@/` alias (`@/features/daemon-status`); use relative paths only inside a slice.
- Tests sit next to the code they test.
- ESLint (`eslint-plugin-boundaries`, in `desktop/eslint.config.js`) enforces these rules in `just lint`.

