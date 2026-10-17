# Working in this repository

Conventions for coding agents (and humans) changing SpoolHQ.

- **Before finishing, run `just lint && just test`** and fix every failure. Do not skip or disable checks to make them pass.
- **Never use `shell=True` or build shell commands from strings.** Call subprocesses with an argument list (`subprocess.run(["git", "status"])`). ruff's `S` rules enforce this in Python.
- **Never commit secrets**: no API keys, tokens, `.env` files or personal paths.
- **Keep changes inside the ticket's scope.** If you find something else that needs doing, note it in the PR description instead of doing it.
- One ticket = one branch (`feat/T<NN>-<slug>`) = one PR. See `CONTRIBUTING.md`.
- Record notable choices in `DECISIONS.md` and add a `PROGRESS.md` entry for each finished ticket.

## Layout

- `daemon/` — Python package `spoolhq` (uv, src layout, Python 3.12+).
- `desktop/` — TypeScript package `@spoolhq/desktop` (pnpm, Node 24 LTS).
- `templates/` — Copier stack templates.
- `docs/` — documentation.
