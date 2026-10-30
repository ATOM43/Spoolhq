# Merge policy

After the reviewer approves a ticket (or says `needs_human`), the merge policy decides whether the work can land by itself or needs a person. It can only add human checks: no setting lets a `needs_human` verdict or a [diff-guard](integration.md#the-diff-guard) refusal go straight to main.

The code is in three parts. The policy itself is `services/runloop/policy.py`: plain values in, a `PolicyDecision` out, no git and no I/O. Its input, the files the squash diff changes with their line counts, comes from `services/git/diffstat.py` (`git diff --cached --numstat -z --find-renames`). The wiring is `services/runloop/approval.py` (the decision during integration, `approve` and `reject`), called from T14's `LocalIntegrator` and T17's `Delivery`.

## When it runs

During [integration](integration.md#the-steps), after main has been merged into the worktree (and the gates rerun if that brought anything), after the squash is staged and the diff guard has passed, and before the commit: the policy sees exactly what would land. SpoolHQ's own `PROGRESS.md` entry, added right after, isn't part of it. A run whose gates failed never gets here (the reviewer only runs after passing gates), and neither does one whose retries ran out, whose agent failed or whose diff the guard refused: those block as before.

## The rules

Every rule is evaluated, and every one that holds is recorded, not just the first.

| Rule | Holds when | Detail |
| --- | --- | --- |
| `needs_human` | the reviewer's verdict is `needs_human` (listed first, so you read the reviewer first) | the reviewer's summary, first 200 characters |
| `review_required` | the ticket has `review_required: true` (set by the planner or you) | `the ticket is marked review_required` |
| `diff_size` | added plus removed lines exceed `merge_policy.max_diff_lines` (default 400). Lockfiles (`uv.lock`, `poetry.lock`, `pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `Cargo.lock`, in any folder) don't count; binary files count as 0 lines | `812 lines > 400` |
| `protected_paths` | any changed, added, deleted or renamed path (the old or the new name) matches a protected pattern | the matching paths, at most 10, then `and N more` |
| `hold_mode` | `run.integration: hold` | `run.integration is hold` |

No rule holds: the ticket goes **direct** (local fast-forward, or a push to GitHub).

### Protected paths

The default list:

- CI and tooling: `.github/**`, `justfile`, `Makefile`, `**/Dockerfile`, `docker-compose*.yml`
- migrations: `**/migrations/**`, `**/alembic/**`
- auth and security: `**/auth/**`, `**/*auth*.py`, `**/security/**`
- dependencies: `**/pyproject.toml`, `**/package.json`, `**/Cargo.toml` and each lockfile above as `**/<name>`
- agent instructions: `CLAUDE.md`, `**/CLAUDE.md`, `.claude/**`, `prompts/**`

Patterns match repo-relative POSIX paths, case-sensitively, the same on every OS. `*` and `?` stay within one folder; `**` matches any number of folders, including none. So `**/migrations/**` matches `migrations/0001.py` and `a/b/migrations/c/d.py` but not `migrationsx/a.py`, `justfile` matches only at the root, and `**/CLAUDE.md` matches `CLAUDE.md` and `backend/CLAUDE.md`.

## Changing it

In `project.yaml` ([reference](project-yaml.md)):

```yaml
merge_policy:
  max_diff_lines: 800                 # 10 to 100,000
  protected_paths_extra: ["infra/**"] # added to the default list
  # protected_paths: ["docs/**"]      # replaces the default list
```

A pattern that is absolute (`/etc/x`, `C:/x`), contains a `..` folder or is empty is refused with the field's name: `project.yaml: merge_policy.protected_paths[0]: must be a repo-relative pattern, got '/etc/x'`.

## What happens

| | With `git.remote` | Without |
| --- | --- | --- |
| no rule holds | pushed to the default branch ([direct mode](github.md#direct-mode-push-before-advancing)) | merged into local main ([integration](integration.md)) |
| a rule holds | a pull request ([PR mode](github.md#pr-mode)) whose body starts with a **Why this needs you** section listing every rule hit | local approval (below) |
| `hold_mode` holds | local approval, as before T18 | local approval |

### Local approval

The squash is undone (the worktree goes back to its branch, nothing is committed), the ticket and the run go to `awaiting_approval` with the worktree kept, and the reason lists the hits:

```text
T04 needs you: diff_size (812 lines > 400), protected_paths (.github/workflows/ci.yml); approve with `spool run approve demo T04` or reject with `spool run reject demo T04 --note "..."` — worktree kept at /home/u/.spoolhq/worktrees/demo/T04
```

```sh
spool run approve <project> <ticket>                 # integrate it (spool run integrate is an alias)
spool run reject <project> <ticket> --note "<text>"  # send it back with your note
```

**Approve** integrates the ticket through the usual path (merge main in, gates if main moved, squash, deliver). The approval is recorded for that attempt (a `log` event with `approved_attempt`), so the policy, run again, lets it through: without a remote it goes direct; with a remote (hold mode), `hold_mode` no longer applies, and any other rule that still holds opens a pull request. The decision is logged with `"approved_by_user": true`. A ticket waiting for another reason (a dirty main checkout, an interrupted integration) is integrated with the policy applied as usual.

**Reject** starts a new attempt of kind `pr_changes` in the kept worktree, with your note in the implementer's prompt under "Note from the user", then gates, reviewer and policy again. A reject without `--note` is refused: `say what should change with --note`.

The API has the same two: `POST /api/projects/{name}/tickets/{id}/approve` (`/integrate` is an alias) and `POST /api/projects/{name}/tickets/{id}/reject` with `{"note": "..."}`. Both return the run; a ticket that isn't waiting gives 409 `T04 is ready, not awaiting approval`.

## The record

Every decision, direct or not, is an event `policy.decision` in the run log, `{"mode": "direct" | "pr" | "approval", "rules": [{"rule", "detail"}, …]}`, and is stored on the run row's `policy` column ([run log](runs.md), schema 7). It shows in:

- `spool run status`: `needs you: diff_size (812 lines > 400), protected_paths (.github/workflows/ci.yml)`
- `spool runs show <project> <run>`: `policy: approval · needs you: …`, or `policy: direct · no rule holds`
- the API's run response: `policy` with `mode`, `rules` and that `summary` line.
