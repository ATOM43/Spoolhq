# Contributing to SpoolHQ

Thanks for helping. SpoolHQ is pre-alpha, so expect things to move.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 for you if needed)
- [Node.js](https://nodejs.org/) 24 LTS
- [pnpm](https://pnpm.io/) — the exact version is pinned in `desktop/package.json` (`packageManager`)
- [just](https://just.systems/)
- git

Linux, macOS and Windows are all supported. On Windows, `just` runs recipes in PowerShell.

## Commands

| Command | What it does |
| --- | --- |
| `just install` | Installs Python and Node dependencies exactly as locked |
| `just lint` | ruff, ruff format check, mypy, ESLint, Prettier check, `tsc --noEmit` |
| `just test` | pytest and Vitest |
| `just dev` | Starts the app (a placeholder for now) |

Run `just lint && just test` before you open a pull request.

## Workflow

- Work is planned as tickets with IDs like `T07`.
- **One ticket = one branch = one pull request.** Keep each PR inside its ticket's scope.
- Branch names: `feat/T<NN>-<slug>`, for example `feat/T07-run-loop`.
- Fill in the pull request template, including the ticket's "Done when" checklist.
- **PRs must pass CI** on Linux, macOS and Windows before they merge.
- Commit in small, logical steps with clear messages.
- Never commit secrets, tokens or machine-specific paths.

## Licence

By contributing you agree that your contributions are licensed under the [Apache-2.0 licence](LICENSE).
