# GitHub delivery

A project with `git.remote` in `project.yaml` delivers approved tickets to GitHub. Without it, nothing changes: tickets merge into the local default branch as in [integration](integration.md).

The code is in three parts. The git mechanics are `services/git/remote.py` (fetch, compare, push, push a tag, delete a remote branch, parse `owner/repo`). The orchestration is `services/runloop/delivery.py` (`delivery_mode`, `Delivery`), on top of T14's `LocalIntegrator` in `services/runloop/integration.py`, which also holds crash recovery.

## Which mode

```python
delivery_mode(ticket, attempt) -> "direct" | "pr"
```

A ticket with `review_required: true` goes through a pull request; every other ticket is pushed directly to the default branch. Every rule for choosing lives in this one function (T18 adds more).

## Git authentication

Fetches and pushes are plain `git fetch` and `git push` through SpoolHQ's git runner, so they use your own setup exactly as a manual `git push` would: your credential helper for an HTTPS remote, your SSH agent for an SSH one. SpoolHQ never writes credentials into git config, URLs or command lines. Hooks stay disabled and git never prompts (`GIT_TERMINAL_PROMPT=0`); a remote that needs a password you haven't stored fails with git's error.

`git.remote` must be a `github.com` URL (`https://github.com/<owner>/<repo>` or `git@github.com:<owner>/<repo>.git`); SpoolHQ reads `owner/repo` from it. It doesn't need a matching `git remote` in your repository: SpoolHQ fetches by URL and stores what it fetched as `refs/spoolhq/remote/<branch>`, so your remotes and remote-tracking branches (`origin/main`) don't change.

## Fetch first

Before integrating, SpoolHQ fetches the remote's default branch and compares it with local `main`:

| Local `main` | What happens |
| --- | --- |
| The same as the remote's | Integration goes on. |
| Behind it | Local `main` is fast-forwarded to it first, with T14's rule: a dirty main checkout (or a rebase or merge in progress) **waits**, and nothing is touched. |
| Has commits the remote doesn't (ahead or diverged) | The ticket is **blocked**, nothing is pushed. |

```text
local main has commits that are not on https://github.com/acme/demo; push or reset them first:
  3f2a9c1 my own work
```

SpoolHQ never pushes your own unpushed commits: the squash commit's parent is always a commit the remote already has, and this is checked again just before the push.

## Direct mode: push before advancing

1. Merge main into the worktree, rerun the gates if that brought anything, and build the squash commit on top of `main` (now equal to the remote's) — all as in [integration](integration.md#the-steps). **Journal: `committed`.**
2. `git push <remote> <commit>:refs/heads/<default_branch>`: a plain push, never `--force`. GitHub refuses it unless it is a fast-forward.
   - **Refused because the remote's main moved** (`[rejected] (fetch first)` or `(non-fast-forward)`): the worktree goes back to its branch and integration starts over with a new fetch, at most 3 times in all (T14's loop); then the ticket is blocked with `main kept moving during integration`.
   - **Any other failure** (a pre-receive hook, branch protection, no permission, no network) blocks the ticket with git's error: `cannot push to https://github.com/acme/demo: git push failed (exit 1): remote: … [remote rejected] (pre-receive hook declined)`. The message never holds credentials; git's output is cut to its last 20 lines.
   - **Journal: `pushed`.**
3. Only now is local `main` fast-forwarded (`merge --ff-only` or `update-ref`, as T14). If it moved or the checkout got dirty in the meantime, it is left alone: the commit is already on GitHub, and the next integration's fetch catches `main` up. **Journal: `advanced`.**
4. Tag `ticket/<id>` and push the tag. A failed tag push is logged, not blocking: the work is delivered, and the tag stays in the local repository. **Journal: `tagged`**, then `done` as in T14.

## What blocks and what waits

| Situation | Result |
| --- | --- |
| Main checkout dirty, or a rebase/merge in progress there | Waits in `awaiting_approval`; `spool run integrate` continues. |
| Local `main` has commits the remote doesn't | Blocked, with the commits listed. |
| The fetch fails (no network, no access) | Blocked: `cannot fetch main from <remote>: <git error>`. |
| The push is refused because main moved, 3 times | Blocked: `main kept moving during integration`. |
| The push fails for any other reason | Blocked, with git's error. |
| The tag push fails | Logged; the ticket is done. |

## Crash recovery

The journal ([integration](integration.md#crash-recovery)) has a state `pushed` between `committed` and `advanced`. At daemon startup, for a project with `git.remote`, every open row with a commit is checked against the remote first:

| Found | Recovery |
| --- | --- |
| After a fetch, the remote's default branch contains the commit | It was pushed. Local `main` is fast-forwarded if it can be (else left for the next fetch), the tag is created and pushed, and the integration finishes as in T14: ticket and run `done`, worktree removed. |
| The remote doesn't have it | It was not pushed: T14's recovery (local `main` hasn't reached it either, so the ticket waits in `awaiting_approval`). |
| The fetch fails | Nothing is done. The row is reported and stays open for the next startup. |

Running recovery twice changes nothing.
