# Working in this repository

Rules for coding agents (and humans) changing SpoolHQ. Details live in the linked `docs/` pages.

## Read first

1. The "What exists" summary at the top of `PROGRESS.md`.
2. The `DECISIONS.md` index.
3. Only the `docs/decisions/<area>.md` files and `docs/` pages your ticket touches, plus `graphify-out/GRAPH_REPORT.md` ([code graph](docs/codegraph.md#spoolhqs-own-graph)).

## Rules

- **Before finishing, run `just lint && just test`** and fix every failure. Do not skip or disable checks to make them pass.
- **Never use `shell=True` or build shell commands from strings.** Call subprocesses with an argument list (`subprocess.run(["git", "status"])`). ruff's `S` rules enforce this in Python.
- **Never commit secrets**: no API keys, tokens, `.env` files or personal paths.
- **Keep changes inside the ticket's scope.** If you find something else that needs doing, note it in your report instead of doing it.
- **Work directly on main. No branches, no pull requests.** See `CONTRIBUTING.md`.
- **No source file over 500 lines** (tests exempt); `just lint` runs `scripts/check_line_limit.py`.
- **Decisions**: record notable choices as a new entry at the bottom of the matching `docs/decisions/<area>.md`, plus one line in the `DECISIONS.md` index (how is at its top; `just lint` checks both agree).
- **Progress**: add a `PROGRESS.md` entry for each finished ticket. Agents started by SpoolHQ leave `PROGRESS.md` alone: SpoolHQ adds the entry from their `<progress>` block when it merges.
- **Code graph**: after the code is final and lint and tests pass, rebuild `graphify-out/` and commit it with the ticket, never `graphify-out/graph.html`. Commands: [docs/codegraph.md](docs/codegraph.md#spoolhqs-own-graph).

## Layers

Full layout and where new code goes: [docs/architecture.md](docs/architecture.md).

- `daemon/` is the Python package `spoolhq` (uv, src layout, Python 3.12+); `desktop/` is `@spoolhq/desktop` (pnpm, Node 24 LTS); `templates/` holds Copier stack templates; `docs/` the documentation.
- Backend: `api/` and `cli/` are thin (validate input, call a service, return the result). `services/` never import FastAPI, Starlette or Typer. `core/` imports nothing from `api/`, `cli/` or `services/`. No service imports `services/runloop`; it may import the others. import-linter enforces this.
- Frontend (Feature-Sliced Design): a layer imports only from layers below it (app → pages → widgets → features → entities → shared); slices on the same layer never import each other; each slice exposes its public API through `index.ts`; cross-slice imports use the `@/` alias, relative paths only inside a slice. ESLint enforces this.

## Testing

How to run and lay out tests: [docs/testing.md](docs/testing.md).

- Daemon tests mirror `src/spoolhq/` ([layout](docs/testing.md#daemon-test-layout)); frontend tests sit next to the code they test.
- Every new function, route or CLI command gets tests in the same change. Every bug fix adds a regression test that fails without the fix.
- Unit tests never use the network, a real model, or the real home folder. The autouse `home` and `projects_dir` fixtures in `daemon/tests/conftest.py` point `SPOOLHQ_HOME` and `SPOOLHQ_PROJECTS_DIR` at tmp dirs; don't bypass them.
- Mark slow or subprocess tests with `@pytest.mark.integration`.
- `just test` fails if daemon line coverage drops below 85%.
