# `project.yaml` reference

Each project's settings live in `~/spoolhq-projects/<name>/project.yaml` (see [Projects](architecture.md#projects)). `spool init` writes one with the defaults filled in; `spool project validate <name>` checks it.

Unknown keys are errors, so a typo never silently falls back to a default.

## Example

```yaml
name: sim-dashboard
repo: ~/code/sim-dashboard
default_branch: main
template:                         # set by spool init --template
  name: fastapi-react
  source: fastapi-react           # built-in name, local folder or git URL
  ref: 0.0.0                      # resolved commit (git), SpoolHQ version (built-in)
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
  max_direct_diff_lines: 400
  protected_paths: ["**/migrations/**", ".github/**", "**/auth/**"]
  always_pr: false
git:
  remote: https://github.com/<owner>/<repo>   # optional
tracker:
  kind: clickup                               # optional
  list_id: "<list id>"
context:
  max_chars: 120000                           # optional: the prompt's size budget
  progress_entries: 3                         # optional: newest PROGRESS.md entries in the prompt
  decisions_lines: 20                         # optional: newest DECISIONS.md lines in the prompt
gates:
  timeouts:                                   # optional, in seconds
    install: 600
    lint: 300
    test: 900
run:
  integration: local                          # local | hold
```

## Fields

| Key | Required | Default | Rules |
| --- | --- | --- | --- |
| `name` | yes | | Slug: `^[a-z0-9][a-z0-9-]{0,62}$` (lowercase letters, digits, hyphens; 1–63 characters). Must match the project's folder name. |
| `repo` | yes | | Absolute path or a path starting with `~`. Must exist and be a git work tree. |
| `default_branch` | no | `main` | A branch name (not a revision such as `main~1` or `main@{0}`) that exists in `repo` (with at least one commit). |
| `template.name` | with `template` | | The template's `name` from its `spoolhq-template.yaml`. The whole `template` block is written by `spool init --template` ([templates](templates.md)). |
| `template.source` | with `template` | | What `--template` was given: a built-in name, a local folder or a git URL. |
| `template.ref` | no | | The resolved commit for a git template (or a local git work tree), SpoolHQ's version for a built-in; left out for a plain folder. |
| `commands.install` | yes | | Non-empty command the gates run to install dependencies. It runs without a shell ([gates](gates.md#no-shell)): no `&&`, `\|\|`, `\|`, `;`, `>`, `<`, `` ` `` or `$(`; put anything longer in a justfile recipe. |
| `commands.lint` | yes | | Non-empty lint command; same rules. |
| `commands.test` | yes | | Non-empty test command; same rules. The planner ends every ticket's "Done when" with `` `<test command>` passes ``. |
| `agents.default` | no | `claude-code-cli` | One of `claude-code-cli`, `codex-cli`, `gemini-cli`, `claude-agent-sdk`. |
| `agents.planner`, `agents.implementer`, `agents.reviewer` | no | `agents.default` | Per-role override; same values as `agents.default`. `agents.planner` is the backend of the [planner](planner.md). Only `claude-code-cli` exists for now. |
| `agents.budget_per_ticket.usd` | no | | Positive number: spending cap per ticket for API backends. |
| `agents.budget_per_ticket.tokens` | no | | Positive whole number: cap on weighted tokens per ticket for subscription backends; one plan generation (both attempts) counts as one ticket. Weighted tokens = input + output + cache writes + cache reads × 0.1, since cache reads cost a tenth of fresh input. T29, for example, used about 2.2M raw tokens (2.1M of them cache reads) but about 300k weighted. `spool runs show` lists the raw numbers and the weighted total. |
| `limits.gate_retries` | no | `3` | Whole number from 0 to 10. |
| `limits.review_retries` | no | `2` | Whole number from 0 to 10. |
| `merge_policy.max_direct_diff_lines` | no | `400` | Whole number above 0. Larger diffs wait for approval in a pull request. |
| `merge_policy.protected_paths` | no | `["**/migrations/**", ".github/**", "**/auth/**"]` | List of globs. A ticket touching one of these waits for approval. |
| `merge_policy.always_pr` | no | `false` | `true` sends every ticket through a pull request. |
| `git.remote` | no | | A GitHub URL: `https://github.com/<owner>/<repo>` (optionally ending in `.git`) or `git@github.com:<owner>/<repo>.git`. The owner is 1–39 letters, digits or hyphens; the repository is 1–100 letters, digits, `.`, `_` or `-`; neither may start with `-` or `.`. |
| `context.max_chars` | no | `120000` | Whole number from 20,000 to 2,000,000: the most characters the implementer's prompt may have ([context](context.md)). |
| `context.progress_entries` | no | `3` | Whole number from 1 to 1,000: how many of the newest `PROGRESS.md` entries the implementer's prompt includes. |
| `context.decisions_lines` | no | `20` | Whole number from 1 to 10,000: how many of the newest non-blank `DECISIONS.md` lines the implementer's prompt includes. |
| `gates.timeouts.install`, `gates.timeouts.lint`, `gates.timeouts.test` | no | `600`, `300`, `900` | Whole number of seconds from 10 to 7,200. When it passes, the gate's whole process tree is stopped ([gates](gates.md#timeouts)). |
| `run.integration` | no | `local` | `local` merges each approved ticket into the default branch as one commit ([integration](integration.md)); `hold` keeps it in `awaiting_approval` until `spool run integrate`. |
| `tracker.kind` | no | `clickup` | Only `clickup` for now. |
| `tracker.list_id` | when `tracker` is set | | Non-empty string; quote it (`"901"`) if it is all digits. |

The commands written by `spool init` are placeholders (`just install`, `just lint`, `just test`); check them before the first run. With `--template`, they come from the template's `spoolhq-template.yaml`, and the template's description is saved next to `project.yaml` as `TEMPLATE.md`, which the [planner](planner.md) reads.

## Errors

Every problem is reported at once, one line each, as `project.yaml: <dotted.path>: <message>`. List items are shown with their index, as in `merge_policy.protected_paths[1]`.

| Problem | Message |
| --- | --- |
| A required key is missing | `project.yaml: commands.test: field required` |
| Unknown key | `project.yaml: limits.gate_retires: unknown key (did you mean 'gate_retries'?)` |
| Bad name | `project.yaml: name: must be 1-63 lowercase letters, digits or hyphens, starting with a letter or digit` |
| Name differs from the folder | `project.yaml: name: 'other' does not match the project folder name 'demo'` |
| Repo path is relative | `project.yaml: repo: must be an absolute path (or start with ~), got 'code/app'` |
| Repo path missing | `project.yaml: repo: path does not exist: /home/me/code/app` |
| Not a git repository | `project.yaml: repo: not a git work tree: /home/me/code/app` |
| Not a branch name | `project.yaml: default_branch: 'main~1' is not a valid branch name` |
| Branch missing | `project.yaml: default_branch: branch 'develop' not found in /home/me/code/app` |
| git not installed | `project.yaml: repo: git was not found on PATH` |
| Bad remote | `project.yaml: git.remote: not a GitHub URL` |
| Unknown backend | `project.yaml: agents.default: unknown backend 'copilot'; expected one of: claude-code-cli, codex-cli, gemini-cli, claude-agent-sdk` |
| Budget not positive | `project.yaml: agents.budget_per_ticket.usd: must be greater than 0` |
| Retries out of range | `project.yaml: limits.gate_retries: must be at most 10` (or `must be at least 0`) |
| Empty command | `project.yaml: commands.lint: must not be empty` |
| Shell syntax in a command | `project.yaml: commands.test: shell syntax isn't supported; put it in a justfile recipe` |
| Unclosed quote in a command | `project.yaml: commands.test: can't be split into arguments: No closing quotation` |
| Unknown integration mode | `project.yaml: run.integration: must be one of 'local' or 'hold'` |
| Gate timeout out of range | `project.yaml: gates.timeouts.test: must be at least 10` (or `must be at most 7200`) |
| Wrong type | `project.yaml: merge_policy.always_pr: input should be a valid boolean, unable to interpret input` |
| YAML syntax error | `project.yaml: line 3, column 1: expected the node content, but found '<stream end>'` |
| Duplicate key | `project.yaml: line 2, column 1: found duplicate key "name" with value "again" (original value: "demo")` |

`spool init` checks its arguments the same way and reports problems without the file prefix, for example `error: repo: not a git work tree: /tmp/x`. It creates nothing unless every check passes.

## How the file is read and written

- The file is parsed with ruamel.yaml's round-trip loader, which never constructs Python objects: a tag such as `!!python/object` is plain data and fails validation.
- When SpoolHQ saves the file, it rewrites only values that changed. Comments, key order and quoting are kept, and settings you left out stay out.
- Saves are atomic (temp file and rename), so a crash never leaves a half-written file.
