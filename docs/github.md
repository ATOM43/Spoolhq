# GitHub delivery

A project with `git.remote` in `project.yaml` delivers approved tickets to GitHub. Without it, nothing changes: tickets merge into the local default branch as in [integration](integration.md).

The code is in three parts. The git mechanics are `services/git/remote.py` (fetch, compare, push, push a tag, delete a remote branch, parse `owner/repo`). The GitHub REST API is `services/github/` (the client with the token, headers, timeouts, rate limits and redaction; pull requests and their reviews; the token lookup), which imports no other service. The orchestration is `services/runloop/`: `delivery.py` (`delivery_mode`, `Delivery`, on top of T14's `LocalIntegrator` in `integration.py`, which also holds crash recovery), `pr_body.py` (the pull request's text) and `polling.py` (`GitHubPoller`).

## Which mode

```python
delivery_mode(ticket, attempt) -> "direct" | "pr"
```

A ticket with `review_required: true` goes through a pull request; every other ticket is pushed directly to the default branch. Every rule for choosing lives in this one function (T18 adds more).

## Git authentication

Fetches and pushes are plain `git fetch` and `git push` through SpoolHQ's git runner, so they use your own setup exactly as a manual `git push` would: your credential helper for an HTTPS remote, your SSH agent for an SSH one. SpoolHQ never writes credentials into git config, URLs or command lines. Hooks stay disabled and git never prompts (`GIT_TERMINAL_PROMPT=0`); a remote that needs a password you haven't stored fails with git's error.

`git.remote` must be a `github.com` URL (`https://github.com/<owner>/<repo>` or `git@github.com:<owner>/<repo>.git`); SpoolHQ reads `owner/repo` from it. It doesn't need a matching `git remote` in your repository: SpoolHQ fetches by URL and stores what it fetched as `refs/spoolhq/remote/<branch>`, so your remotes and remote-tracking branches (`origin/main`) don't change.

## The GitHub token

The GitHub API (opening pull requests and polling them) needs a token; git itself doesn't. SpoolHQ looks for it in this order:

1. `SPOOLHQ_GITHUB_TOKEN` in the daemon's environment.
2. The OS keychain, through [keyring](https://pypi.org/project/keyring/): service `spoolhq`, key `github` (macOS Keychain, Windows Credential Locker, the Secret Service on Linux).

```sh
spool secrets set github     # asks for the token without echoing it; never from the command line
```

The token goes only into the `Authorization` header of API requests. It is never logged (the daemon log redacts it, as it does the daemon's own token), never written to the workspace, the run files or git config, never put in a URL or on a command line, and every API error message has it replaced with `[redacted]`. Direct mode works without a token; PR mode without one blocks the ticket before anything is pushed:

```text
PR mode needs a GitHub token; run spool secrets set github or set SPOOLHQ_GITHUB_TOKEN
```

A fine-grained token needs read and write access to the repository's **Pull requests** (and read access to its metadata). API calls use `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28` and 30-second timeouts.

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

## PR mode

1. Fetch first, merge, gates and the squash commit exactly as in direct mode.
2. Push the commit to the branch `spoolhq/<id>-<slug>` (the run branch's name from [git](git.md#paths-and-branch-names), with `spoolhq/` for `feat/`): a plain push. If that branch already exists on GitHub with other commits, the ticket is blocked: delete the branch there and integrate again. **Journal: `pushed`.**
3. Open a pull request against the default branch:
   - **Title:** `<id>: <title>`, one line, as the squash commit's subject.
   - **Body:** the title; the ticket's `## Purpose` (else its `## Scope`); the "Done when" list with the reviewer's verdict and reason for each item; a table of the gates (command, pass/fail, duration); and the run id. All ticket and agent text is escaped: markdown specials are backslash-escaped and `&`, `<`, `>` and `@` become HTML entities, so markup and HTML show as text and nobody is mentioned. The body is cut at 60,000 characters.
   - If GitHub refuses it, the pushed branch is deleted again and the ticket is blocked with `cannot open a pull request: <the API error>`.
4. The PR's number, URL and branch are stored on the run (run log schema 6), the journal row becomes `pr_open`, the worktree and its local branch are removed (the branch on GitHub holds the work), and the ticket and run wait in `awaiting_approval`: `T04 · PR #12 opened: https://github.com/acme/demo/pull/12`. `spool run all` stops there, as with any ticket that waits.

`spool run status` and `spool tickets show` show the pull request, and the API's run views carry `pr_number` and `pr_url`. `spool run integrate` refuses such a ticket (`T04 waits on PR #12: …`): it is merged on GitHub.

## Polling pull requests

While the daemon runs, it checks the open pull requests of every project every 60 seconds; `spool github sync <project>` does it at once and prints a line per pull request. A pull request is open for SpoolHQ while its ticket's latest run waits in `awaiting_approval` with a PR number. Only SpoolHQ's own pull requests are read.

| GitHub says | What happens |
| --- | --- |
| Merged | Fetch; fast-forward local `main` if it is behind (a dirty main checkout **waits** for the next poll, untouched); tag `ticket/<id>` on the PR's merge commit and push the tag; delete the PR branch; ticket and run `done`; the journal row `done` with the merge commit (so `spool run status` shows it as last merged). The `PROGRESS.md` entry is already in the squash commit. |
| A `CHANGES_REQUESTED` review newer than the last attempt | A new attempt, of kind `pr_changes`, in a worktree recreated from the PR branch's head. Its prompt includes the review's body and its inline comments (file and line), as untrusted text in their own fenced block inside the escaped `<previous_attempt>` block ([context](context.md)). Then the gates and the reviewer as usual; once approved, the new commits are pushed on top of the same branch, a fast-forward, never forced, and the ticket waits again. The pull request stays open. If the branch moved on GitHub in the meantime, the ticket is blocked rather than forced. |
| Closed without merging | Ticket and run `blocked`: `PR #12 was closed without merging`. |
| Still open, nothing new | Nothing. |

A review is answered once: the attempt records the review's id. A new attempt waits while another run is active in the project or the main checkout isn't clean, and is tried again at the next poll.

**API errors and rate limits never block a ticket.** A failed call is logged and the next poll tries again. A rate limit (`429`, or `403` with `X-RateLimit-Remaining: 0`) stops all calls until the time GitHub gave (`Retry-After`, else `X-RateLimit-Reset`, else 60 seconds). Untrusted text from the API (review bodies, comments) never reaches a shell, a template or git; branch names come from SpoolHQ's run log, not from the API.

## What blocks and what waits

| Situation | Result |
| --- | --- |
| Main checkout dirty, or a rebase/merge in progress there | Waits in `awaiting_approval`; `spool run integrate` continues. |
| Local `main` has commits the remote doesn't | Blocked, with the commits listed. |
| The fetch fails (no network, no access) | Blocked: `cannot fetch main from <remote>: <git error>`. |
| The push is refused because main moved, 3 times | Blocked: `main kept moving during integration`. |
| The push fails for any other reason | Blocked, with git's error. |
| The tag push fails | Logged; the ticket is done. |
| PR mode without a GitHub token | Blocked, before anything is pushed. |
| The PR branch already exists with other commits | Blocked. |
| Opening the pull request fails | Blocked; the pushed branch is deleted again. |
| The PR waits for review | Waits in `awaiting_approval`. |
| The PR is merged but the main checkout is dirty | Waits; the next poll finishes it. |
| The PR is closed without merging | Blocked. |
| A GitHub API error or rate limit while polling | Nothing changes; the next poll tries again. |

## Crash recovery

The journal ([integration](integration.md#crash-recovery)) has a state `pushed` between `committed` and `advanced`. At daemon startup, for a project with `git.remote`, every open row with a commit is checked against the remote first:

| Found | Recovery |
| --- | --- |
| After a fetch, the remote's default branch contains the commit | It was pushed. Local `main` is fast-forwarded if it can be (else left for the next fetch), the tag is created and pushed, and the integration finishes as in T14: ticket and run `done`, worktree removed. |
| The remote doesn't have it | It was not pushed: T14's recovery (local `main` hasn't reached it either, so the ticket waits in `awaiting_approval`). |
| The fetch fails | Nothing is done. The row is reported and stays open for the next startup. |

Running recovery twice changes nothing.

A pull request's row is `pr_open` once it is opened, so recovery leaves it alone; the poller finishes it. A crash between the push to the PR branch and opening the pull request leaves the branch on GitHub: the ticket waits as interrupted, and integrating again is blocked until the branch is deleted there.

## Tests

`tests/services/git/test_remote.py` and `tests/services/runloop/test_delivery.py` use a local bare repository as the remote: `url.<bare>.insteadOf https://github.com/acme/demo` in the test repository's config makes git use it, so no network is involved. `tests/services/runloop/test_pull_requests.py` adds `FakeGitHub`, an `httpx.MockTransport` that serves the pull request API and merges through the bare repository. Tests never read the real keychain: an autouse fixture installs an in-memory one (and `PYTHON_KEYRING_BACKEND` points subprocesses at keyring's null backend).

`tests/services/runloop/test_github_real.py` (`integration`, opt-in) pushes one ticket directly and opens one pull request (then closes it) against a real throwaway repository: set `SPOOLHQ_GITHUB_TEST_REPO=https://github.com/<you>/<repo>` and `SPOOLHQ_GITHUB_TEST_TOKEN`, with git able to push there through your own credential helper or SSH agent.
