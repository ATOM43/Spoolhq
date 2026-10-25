# Templates

A template is a project skeleton that `spool init --template` generates a new repository from. The generated repo already installs, lints and tests clean, so the planner starts from real work instead of setup. Templates are [Copier](https://copier.readthedocs.io/) templates with one extra file, `spoolhq-template.yaml`, that tells SpoolHQ the template's name, a description for the planner and the gate commands.

The code is `services/templates/`: the contract in `contract.py`, sources in `sources.py`, the Copier call, git init and first commit in `generate.py`, and the contract check in `check.py`. It may import `services.projects`, `services.gates` and `services.git` (an import-linter contract forbids the rest). `spool init` (in `cli/main.py`) and `spool templates list|check` (in `cli/templates.py`) call it directly.

## Sources

`--template` (and `spool templates check`) take one of:

| Source | Looks like | `template.ref` in `project.yaml` |
| --- | --- | --- |
| A built-in name | `fastapi-react`: no `/`, `\`, leading `.` or `~` | SpoolHQ's package version |
| A local folder | `./my-template`, `~/templates/api`, `/srv/tpl` | the folder's `HEAD` commit if it is a git work tree (Copier then renders `HEAD` with uncommitted changes), otherwise none |
| A git URL | a URL with a scheme (`https://`, `ssh://`, `file://`), `git@host:path`, `gh:owner/repo`, or anything ending in `.git` (a local bare repo works) | the resolved commit |

Built-ins ship inside the package, under `daemon/src/spoolhq/templates/<name>/` (package data, like the prompt templates). `spool templates list` shows them with their descriptions. An unknown name is refused with `unknown template 'x'; spool templates list shows the built-in ones`.

For a git URL, SpoolHQ clones it once with its own git runner (hooks disabled), resolves `--template-ref` (a branch, tag or commit; without it, the repository's default branch) to a commit, and prints the source and commit **before generating**:

```text
template: https://github.com/me/tpl.git at commit 3f2a…
```

Copier then renders exactly that commit. `--template-ref` with anything but a git URL is an error.

## The contract: `spoolhq-template.yaml`

At the template root; it is never copied into the generated project (SpoolHQ passes it to Copier's `exclude`, and templates should list it in `_exclude` too).

```yaml
name: fastapi-react
description: >   # given to the planner; plain text, at most 2,000 characters
  A FastAPI backend and a React frontend ...
commands:
  install: just install
  lint: just lint
  test: just test
  dev: just dev     # optional
```

| Key | Required | Rules |
| --- | --- | --- |
| `name` | yes | Slug, like a project name. Used in the first commit's message. |
| `description` | yes | Non-empty plain text, at most 2,000 characters. Saved as the workspace's `TEMPLATE.md`; the planner reads it. |
| `commands.install`, `commands.lint`, `commands.test` | yes | Copied into `project.yaml`'s `commands`. Same rule as there: no shell syntax (`&&`, pipes, redirects…), see [gates](gates.md#no-shell). |
| `commands.dev` | no | Same rule. Documentation only: SpoolHQ never runs it and `project.yaml` doesn't store it. |

Unknown keys are errors. Every problem is reported at once, one line each, in `project.yaml`'s style:

| Problem | Message |
| --- | --- |
| No file | `template 'x': no spoolhq-template.yaml at the template root; every template must have one (docs/templates.md)` |
| A gate command missing | `template 'x': spoolhq-template.yaml has no 'test' command; every template must declare install, lint and test` |
| Shell syntax | `template 'x': spoolhq-template.yaml: commands.lint: shell syntax isn't supported; put it in a justfile recipe` |
| Description too long | `template 'x': spoolhq-template.yaml: description: must be at most 2,000 characters, got 2,001` |
| Other field problems | `template 'x': spoolhq-template.yaml: <dotted.path>: <message>` |

`'x'` is the built-in name, the folder name or the repository name.

## No trust

Templates are code, so they get no trust. SpoolHQ never passes Copier's `unsafe`/`--trust`, and it gives Copier empty settings, so a trusted prefix in the user's own Copier settings (`COPIER_SETTINGS_PATH` or `~/.config/copier/settings.yml`) doesn't apply either. A template whose `copier.yml` (any of its YAML documents) sets `_tasks`, `_migrations` or `_jinja_extensions` is refused before anything is generated:

```text
template 'x' needs Copier tasks or extensions, which SpoolHQ doesn't run
```

Copier's own unsafe check runs too, so tasks or extensions pulled in through `!include` are refused with the same message. Copier (9.19.1) renders with its `SandboxedEnvironment`, a subclass of Jinja2's sandbox that also hides Pydantic's `parse_file`/`parse_raw`, Copier's settings loader and `PurePath.parser`; its loader refuses `{% include %}` of files outside the template root, and symlinks that point outside the template are refused unless the template sets `_preserve_symlinks` (then they are copied as links). What remains is what any template can do: write files into the new repository. The generated project's own `install`, `lint` and `test` then run as [gates](gates.md), which are not sandboxed yet.

## What `spool init --template` does

```sh
spool init <name> --repo <path> --template <source> [--template-ref REF] [--branch main] [--remote URL]
```

1. Checks the name and that the workspace doesn't exist. `--repo` must not exist or be an empty folder; anything else is refused and left untouched (`--repo must be a new or empty folder: … is not empty`).
2. Resolves the source (printing it, with the commit for git), reads the contract and refuses unsafe features. Nothing has been written yet.
3. Runs Copier non-interactively with the template's defaults and `project_name` set to the project name.
4. `git init --initial-branch=<branch>`, stages everything and makes the first commit `chore: apply template <name>` through the integration commit helper: hooks and signing disabled, nothing written to any git config. The commit needs your git identity (`user.name`/`user.email`, or the `GIT_AUTHOR_*`/`GIT_COMMITTER_*` variables). Copier's answers file, `.copier-answers.yml`, is committed, so `copier update` can work later (SpoolHQ doesn't run it).
5. Creates the workspace like `spool init` does, with `commands` from the contract, a `template` block (`name`, `source`, `ref`; see [project-yaml](project-yaml.md)) and the description in `TEMPLATE.md`.

Any failure after generation started removes what was generated (the folder if SpoolHQ created it, its contents if it was empty before) and reports what failed, followed by `removed what was generated in <path>`; the workspace is created all or nothing, so none is left behind.

## The contract check

```sh
spool templates check <source> [--ref REF]
```

Generates the template into a temp folder (project name: the template's `name`), runs `git init` and stages the files (no commit, so no identity is needed), then runs the declared `install`, `lint` and `test` as [gates](gates.md), with the default timeouts. It prints the log folder, the source, each gate like `spool gates run` (and the failures' excerpts), and `template '<name>' passes its contract (<seconds> s)`. Exit 0 only when all three pass. The temp folder is removed afterwards; the logs stay.

The built-in templates are checked in SpoolHQ's CI on Linux, macOS and Windows (`daemon/tests/services/templates/test_fastapi_react.py`).

## Writing a template

1. A Copier template folder (or git repository) with a `copier.yml`. Use `_templates_suffix: .jinja` so only `*.jinja` files are rendered and everything else (TSX, GitHub workflows with `${{ }}`) is copied as is.
2. Declare a `project_name` question with a default; SpoolHQ answers it. Every other question must have a default, since nothing is asked.
3. Add `{{_copier_conf.answers_file}}.jinja` containing `{{ _copier_answers|to_nice_yaml -}}`, so the answers file is written.
4. Set `_exclude` to keep `spoolhq-template.yaml` out of the project. `_exclude` replaces Copier's defaults, so repeat them (`copier.yml`, `~*`, `*.py[co]`, `__pycache__`, `.git`, `.DS_Store`).
5. No `_tasks`, `_migrations` or `_jinja_extensions`. Lockfiles belong in the template, so `install` can run locked.
6. Write `spoolhq-template.yaml`. Make the description say what exists and where new work goes: the planner treats the template's setup as done.
7. Run `spool templates check <folder>` until it passes.

A built-in template also goes in `daemon/src/spoolhq/templates/<name>/`; that folder is excluded from SpoolHQ's own ruff and mypy (it has its own lint setup).

## `fastapi-react`

The first built-in: a FastAPI backend (`backend/`: SQLAlchemy 2 on SQLite, Alembic, pytest with an 80% coverage floor, ruff with `S`, mypy strict, `app/api` on top of `app/services/<domain>` on top of `app/core`, enforced by import-linter) and a React frontend (`frontend/`: Vite, strict TypeScript, Vitest and Testing Library, ESLint and Prettier, Feature-Sliced Design enforced by eslint-plugin-boundaries), with an example `items` domain through every layer, a justfile (`install`, `dev`, `lint` with a 500-line check, `test`), GitHub Actions CI, `CLAUDE.md`, `PROGRESS.md` and `DECISIONS.md`. The generated project's `README.md` describes its structure. Every dependency is pinned, in `backend/pyproject.toml` and `uv.lock` and in `frontend/package.json` and `pnpm-lock.yaml`.
