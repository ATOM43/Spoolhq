# Git

Every run of a ticket works in a disposable git worktree of the project's repository, on its own branch. The main working copy is never touched: SpoolHQ only reads it, adds and removes worktrees, creates and deletes its own branches, and keeps one config entry per branch. There is no fetch or push yet (T17 adds remotes) and nothing merges into the default branch yet (T14). The run loop ([run-loop.md](run-loop.md)) drives these APIs.

The code is `services/git/`: the git runner in `runner.py`, branch names in `naming.py`, main-repository checks in `repo.py`, `WorktreeManager` in `worktrees.py` and crash recovery in `recovery.py`. It imports no other service package (an import-linter contract checks this); what it needs from the run log is passed in as a callable.

## One worktree per run

A **run** gets one worktree, created when the run starts and removed when it ends. Gate and review retries inside the run (its attempts) continue in the same worktree, so the implementer fixes its own work instead of starting over. A ticket has at most one worktree at a time: `create` refuses a second one with

```text
T04 already has a worktree at /home/u/.spoolhq/worktrees/demo/T04; resume it or remove it first
```

and `resume(ticket_id)` returns the existing one (if git has it registered, its folder exists and its branch carries the marker), with `base_sha` set to the merge-base of the branch and the default branch.

## Paths and branch names

| What | Where |
| --- | --- |
| Worktree | `~/.spoolhq/worktrees/<project>/<ticket_id>` |
| Branch | `feat/<ticket_id>-<slug>` |
| Base | the local default branch from `project.yaml` (`default_branch`), as it is when the worktree is created |

The worktree root is the `worktrees_dir` setting (`config.toml` or `SPOOLHQ_WORKTREES_DIR`), by default `worktrees/` in the SpoolHQ home folder.

Ticket titles are untrusted text. The slug is built from the title by these steps:

1. NFKD-normalise, then drop every non-ASCII character (`é` → `e`).
2. Lowercase.
3. Replace each run of characters outside `a-z0-9` with `-`, then strip `-` from both ends.
4. Cut to 40 characters, then strip a trailing `-` again.
5. If nothing is left, use `ticket`.

| Title | Branch for T04 |
| --- | --- |
| `Fix "quoted" thing; rm -rf /` | `feat/T04-fix-quoted-thing-rm-rf` |
| `Café über ünïcode` | `feat/T04-cafe-uber-unicode` |
| ``$(touch pwned) && `id` `` | `feat/T04-touch-pwned-id` |
| `;;;""''` | `feat/T04-ticket` |
| 39 × `a` + `-b` | `feat/T04-aaa…a` (39 × `a`: the cut leaves a trailing `-`, which is stripped) |

The ticket id must match the ticket id pattern (`T` and 2–3 digits), and every name is confirmed with `git check-ref-format --branch` before it is used. A name git refuses would be a bug in the slug rules and raises.

Titles, ids, paths and commit messages reach git only as separate arguments of an argument list, never through a shell.

## The ownership marker

When SpoolHQ creates a branch, it records the run in the main repository's config:

```sh
git config branch.feat/T04-say-hi.spoolhq 12     # 12 = the run id
```

SpoolHQ deletes or recreates **only branches that carry this marker**. `git branch -D` removes the branch's config section, marker included.

- A marked branch that is checked out nowhere (left by an earlier run) is deleted and recreated from the default branch, with the log line `recreating stale SpoolHQ branch feat/T04-…`.
- A marked branch that is checked out in another worktree is refused: `branch feat/T04-… is checked out at …; remove that worktree first`.
- A branch with the same name but no marker is somebody's work, and is never touched: `branch feat/T04-… exists and was not created by SpoolHQ; rename or delete it`.

## Checks before a worktree is created

`create` first checks the main repository, and changes nothing if a check fails:

- **Nothing in progress.** A rebase, merge, cherry-pick or revert in progress (the paths `git rev-parse --git-path` gives for `rebase-merge`, `rebase-apply`, `MERGE_HEAD`, `CHERRY_PICK_HEAD` and `REVERT_HEAD`) is refused:

  ```text
  repo /home/u/code/x: a rebase is in progress; finish or abort it first
  ```

- **Clean.** `git status --porcelain=v1 -z --untracked-files=normal` must be empty: any modified, staged or untracked file that isn't ignored is refused. Up to 20 entries are listed, then `… and N more`:

  ```text
  repo /home/u/code/x has uncommitted changes; commit or stash them first:
     M src/a.py
    ?? notes.txt
  ```

- **The default branch exists.** `git rev-parse --verify --quiet refs/heads/<branch>^{commit}`, else `default branch 'main' not found in /home/u/code/x`.

Then `git worktree add -b <branch> <path> <base_sha>` creates the worktree and the marker is set. If anything fails after `worktree add`, the worktree, its folder and the new branch are removed again before the error is raised.

## Commits

`commit_all(wt, message)` runs `git add -A`; if `git diff --cached --quiet` finds nothing staged it returns `None`, otherwise it commits with `git commit --no-verify -m <message>` and returns the new sha. The message is one argument and is stored verbatim.

The commit runs with `user.useConfigOnly=true`, so git never invents an identity from the user and host names. Without `user.name` and `user.email` it raises `git user.name/user.email not set for /home/u/code/x; set them with git config`.

## Hooks and signing

**SpoolHQ's own git calls never run repository hooks and never sign.** `run_git` puts these options before every subcommand:

```text
-c core.hooksPath=<home>/hooks-disabled
-c commit.gpgsign=false
-c tag.gpgsign=false
-c tag.forceSignAnnotated=false
```

A `-c` on the command line wins over the repository's, the user's and the system's config, so neither can turn hooks or signing back on.

**Why hooks:** the agent works inside a worktree of the repository. If the repository sets `core.hooksPath` to a tracked folder (`.husky`, `.githooks`), that folder is in the worktree too, and the agent can write a new hook there. The next git command SpoolHQ runs (`git worktree add` runs `post-checkout`; `git commit` runs `prepare-commit-msg` and `post-commit`) would then run that code as the daemon, outside the agent's permission policy: a sandbox escape. `--no-verify` is not enough, because it skips only `pre-commit` and `commit-msg`. Hooks in `.git/hooks/` are code SpoolHQ doesn't control either: they can hang, prompt, need tools that aren't installed, or change files after the gates (T11), which are SpoolHQ's checks, have passed.

`<home>/hooks-disabled/` is created on first use and must stay empty: `run_git` lists it with `os.scandir` before every call, and if anything is in it, it starts no git process and raises `<path> must be empty; SpoolHQ uses it to disable git hooks`. Commits still pass `--no-verify` as well, in case a future call ever bypasses `run_git`.

**Why signing:** with `commit.gpgsign=true` or `tag.gpgsign=true` in the user's config, git would try to sign SpoolHQ's commits and tags and can wait on a passphrase prompt until the 60 s timeout, or fail if the signing program is missing. SpoolHQ's commits are unsigned; signing may come back later as an opt-in.

**What this does not cover:**

- **git config filters** (`filter.<driver>.clean` / `smudge`, set through `.gitattributes`) and similar config-driven programs. They are not hooks, so `core.hooksPath` does not stop them.
- **The agent's own git commands.** What the agent may run, git included, is decided by its permission policy (T09), not by `run_git`.

## Teardown

`teardown(wt_or_ticket_id, delete_branch=True)`:

1. `git worktree remove --force <path>`.
2. If the folder still exists (on Windows, a file lock or a read-only file can stop git), `shutil.rmtree` deletes it; its error handler clears the read-only bit on the path and its folder and retries once.
3. `git worktree prune`.
4. If `delete_branch` is set and the branch carries the marker, `git branch -D <branch>`.

With nothing left to remove it only prunes, so calling it twice is safe. Each step is logged.

**Teardown always runs.** `session(ticket_id, title, run_id)` is a context manager that yields the worktree and tears it down when the block ends, normally or by an exception (a teardown failure after an exception is logged, so the original exception is the one raised). Calling `keep()` on the yielded worktree leaves it in place: a blocked run keeps its worktree for inspection.

```python
with manager.session("T04", ticket.title, run.id) as wt:
    ...                       # the agent works in wt.path
    manager.commit_all(wt, f"T04: {ticket.title}")
    if blocked:
        wt.keep()
```

`spool worktrees list <project>` shows each worktree under the project's root with its ticket, branch, path and state:

| State | Meaning |
| --- | --- |
| `ok` | registered with git, folder present, branch marked |
| `missing folder` | registered, but the folder is gone |
| `not registered` | a folder git doesn't know |
| `no marker` | registered, but its branch has no SpoolHQ marker |

It only reads; cleanup happens when the daemon starts.

## Crash recovery

A daemon that stops mid-run leaves its worktree behind. At startup, after the run log's recovery ([runs.md](runs.md#recovery)), the daemon runs `recover_worktrees` for every workspace whose `project.yaml` loads. Its `keep(ticket_id)` callable is true when the ticket's latest run is `blocked` or `awaiting_approval` (those worktrees wait for a person) or `interrupted` (the run loop resumes from its commits). Recovery in the run log has just marked every run a stopped daemon left `running` or `paused` as `interrupted`, so a crash, reboot or restart keeps that run's worktree and branch.

1. `git worktree prune` drops registered worktrees whose folder is gone: **pruned**. Their branch stays; the next `create` for the ticket recreates it if it is marked.
2. Each registered worktree under `<root>/<project>/` whose ticket isn't kept is torn down: **removed**. Its branch is deleted only if it carries the marker.
3. Each folder under `<root>/<project>/` that git doesn't know, and whose ticket isn't kept, is deleted: **removed_orphan**.
4. The rest are **kept**. One that can't be removed is **failed**, with the error as its reason.

Only entries named like a ticket id directly under `<root>/<project>/` are considered. Worktrees anywhere else are never touched, and a branch without the marker is never deleted. The report lists every entry with its path and reason, and each gets one log line (`worktree removed`, with project, ticket and reason). A second run finds nothing new.

A workspace whose repository is missing or whose git fails is logged as an error naming the project and skipped; startup continues. Ticket statuses are not changed here: an interrupted ticket stays `running` until `spool run resume` or `spool run discard` ([run-loop.md](run-loop.md)).

## git version

SpoolHQ needs **git 2.36 or newer**, the first with `git worktree list --porcelain -z` (NUL-separated, so any path parses). The daemon checks `git --version` once at startup; an older git is logged as an error (`git 2.36 or newer is required (found 2.34.1)`) and the daemon keeps serving.

## How git is run

Every call goes through `run_git(args, cwd, timeout=60)` in `runner.py`:

- An argument list (`subprocess.run([git, ...])`), never a shell. `git` is found once with `shutil.which`; if it is missing: `git not found on PATH`.
- `-c core.quotepath=off -c core.fsmonitor=false` before every subcommand, so paths come back unescaped and no fsmonitor daemon is started, plus the hook and signing overrides from [Hooks and signing](#hooks-and-signing).
- The environment is a copy of the daemon's with `GIT_TERMINAL_PROMPT=0` (never prompt), `GIT_OPTIONAL_LOCKS=0` (reads don't take the index lock), `LC_ALL=C` and `LANGUAGE=C` (stable messages). Variables that point git at another repository (`GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, …) are removed, and stdin is empty.
- Output is decoded as UTF-8 with `errors="replace"`.
- A failure raises `GitError` with the arguments, the exit code and the last 20 lines of stderr: `git worktree add failed (exit 128): fatal: …`.
