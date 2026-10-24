# Run loop

The run loop takes one ready ticket through its worktree, the implementer, the gates and the reviewer, with retries, and either hands an approved attempt to integration or blocks the ticket. It lives in the daemon: a run executes in a worker thread there, so it survives the terminal that started it and can be paused, resumed or cancelled from another one.

The code is `services/runloop/`: the values (`RunContext`, `Ending`, `Flags`, the errors) in `model.py`, the state machine as plain functions over a `RunContext` in `machine.py`, `RunLoop` (start, pause, resume, cancel, discard, current) in `loop.py`, the integration seam in `integrator.py`, the per-project lock in `lock.py` and the usage-limit timer in `resume.py`. It is the one service allowed to import the others (scheduler, tickets, projects, runs, git, agents, context, gates, review); no service imports it, only `api/` and `cli/` do, which an import-linter contract checks.

## The state machine

For each run:

1. **Pick.** `next_ready()` ([scheduler](scheduler.md)), or the ticket named by the user if it is `ready`. The main repository must be clean with nothing in progress, or nothing starts. The ticket moves to `running`, the run row is created (`run.started`) and the worktree with its branch ([git](git.md)): one worktree per run, so every retry builds on the earlier attempts' work.
2. **Implement.** A new attempt row (`initial`, `gate_retry`, `review_retry` or `conflict_retry`). The prompt is rendered ([context](context.md)); on a retry its `<previous_attempt>` block is read from the last finished attempt's `gates.json` and `review.json`: the failing tests and failing gates, or the review items that are not met with their reasons. The implementer runs with the writing policy ([agents](agents.md)) and a budget of 100 turns, 30 minutes and, if the project has a token budget, the tokens left. Its `<progress>` note is taken from the full final text (not the 4,000-character summary) and stored on the run for integration.
3. **Commit.** SpoolHQ commits everything in the worktree on the run's branch, as `spool: T04 attempt 2`, with hooks and signing disabled (T08's `commit_all`); the agent never commits. The files changed come from git (`git diff --name-only`), not from the agent's edit events. `diff.patch` gets `git diff <base>...HEAD`.
4. **Gates** ([gates](gates.md)), their logs in the attempt folder and the results in `gates.json`. If any gate fails: the attempt ends `gates_failed`; with gate retries left, a `gate_retry` attempt starts at step 2, else the run is blocked: `gates failed after 3 retries: just test` (the first failing gate's command).
5. **Review** ([review](review.md)) of `git diff <base>...HEAD`, with the items the gates checked taken from `check_done_when`. The worktree's `HEAD` and `git status` must be the same before and after; if not, the run is blocked with `reviewer changed the worktree`. The verdict goes to `review.json`.
   - `approve`: the attempt ends `approved`; step 6.
   - `changes_requested`: with review retries left, a `review_retry` attempt starts at step 2 with the unmet items as review notes, else blocked: `changes requested after 2 retries`.
   - `needs_human`: blocked at once: `the reviewer asked for a person: <summary>`.
6. **Integrate.** The `Integrator` gets the approved run (see [The integration seam](#the-integration-seam) and [integration.md](integration.md)). A merge conflict with main starts one `conflict_retry` attempt; gates failing on the merged code start a `gate_retry`.

Before each attempt the loop checks `agents.budget_per_ticket` (tokens and/or USD) against the run's total usage; when it is used up the run is blocked: `budget used up: 2,104,331 of 2,000,000 tokens` (or `budget used up: $2.10 of $2.00`).

Each phase change is a `run.phase` event whose `text` is the line `spool run` prints:

```text
T04 · Project workspace · run 12
T04 · worktree · /home/u/.spoolhq/worktrees/demo/T04
T04 attempt 1 · implement (initial)
T04 attempt 1 · commit · 3f2a9c1 (3 files)
T04 attempt 1 · gates · ✗ test (2 failing)
T04 attempt 2 · implement (gate_retry)
T04 attempt 2 · commit · 81d0e4b (1 files)
T04 attempt 2 · gates · ✓ passed
T04 attempt 2 · review · approve
T04 · integrate · merged 3f2a9c1 · ticket/T04
T04 · done
```

The attempt folder `runs/<ticket>/<NNN>/` holds `transcript.jsonl` (the implementer's and then the reviewer's raw stream), `gates.json` and the gate logs, `diff.patch` and `review.json`. Token usage is recorded per attempt, so `run_usage` sums it per run.

## Counting retries

- `limits.gate_retries` (default 3) counts gate rounds only, `limits.review_retries` (default 2) review rounds only. A gate retry doesn't reset the review counter, nor the other way round.
- The counters are the number of the run's `gate_retry` or `review_retry` attempts, read from the attempt rows, so a resumed run counts exactly like one that never stopped.
- An `interrupted` attempt (cut off by a usage limit, a pause or a crash) never counts. The attempt that resumes it has the same kind and counts once.

## Agent outcomes

| Outcome | Implementer | Reviewer |
| --- | --- | --- |
| `completed` | commit, then gates | the verdict decides |
| `usage_limited` | attempt `interrupted`, run `paused` with `reset_at` | same |
| `timed_out`, `max_turns`, `budget_exhausted` | the work so far is committed; attempt `error`; uses a gate retry (blocked if none left: `implementer stopped (max_turns) after 3 retries`) | attempt `changes_requested`; uses a review retry |
| `error` (a policy violation included) | blocked at once with the error text; never retried | same |
| `cancelled` | see [Cancel](#cancel) | same |

After an early stop the next prompt's `<previous_attempt>` says so (`Your last attempt stopped before the checks ran (max_turns)…` or `The reviewer stopped before giving a verdict…`), under the template's "Note from SpoolHQ" heading; "Note from the user" is only for what a user wrote.

## Paused, blocked, cancelled, interrupted

| Run status | How | Ticket | Worktree | What next |
| --- | --- | --- | --- | --- |
| `paused` | a usage limit, or `spool run pause` | `running` | kept | resumes by itself at `reset_at` + 60 s (usage limit, daemon running), or `spool run resume` |
| `blocked` | retries used up, `needs_human`, an agent error, budget used up, the reviewer changed the worktree, an internal error | `blocked` | kept, for inspection | fix it, then `spool run discard` and run again |
| `cancelled` | `spool run cancel` | `ready` | removed, with its branch | — |
| `interrupted` | the daemon stopped while the run was active ([runs](runs.md#recovery)) | `running` | kept | `spool run resume`, or `spool run discard` |
| `awaiting_approval` | approved, and held (`run.integration: hold`), waiting for a clean main checkout, or its integration was interrupted | `awaiting_approval` | kept | `spool run integrate` |
| `done` | approved and merged | `done` | removed | — |

**Usage limits pause, never block.** When the implementer or the reviewer returns `usage_limited`, the current attempt becomes `interrupted`, the run `paused` with `reset_at` stored on the run row, and the daemon schedules a resume at `reset_at` plus 60 s. The timer reads the loop's clock once a second on its own thread and is cancelled when the daemon shuts down. Without a known `reset_at`, the run waits for `spool run resume`.

**Pause** waits for the current agent call to finish (its work is committed), then stops before the next step. The attempt it stopped is `interrupted`, so resume starts a new attempt of the same kind, which doesn't count against the retries. A paused run still counts as the project's active run.

**Resume** continues a `paused` run, or the newest `interrupted` run whose ticket is still `running`, in its kept worktree (`WorktreeManager.resume`). An interrupted run is reopened (`RunLog.reopen_run`: `interrupted` → `running`, the only way out of a terminal status). The next attempt's kind comes from the last attempt: an `interrupted` one is repeated, `gates_failed` (or an implementer `error` from an early stop) gives `gate_retry`, `changes_requested` gives `review_retry`, and an `approved` one only integrates. If the worktree is gone, the run is blocked: `the worktree of T04 is gone; discard it with spool run discard T04`.

**Crash recovery.** At startup the run log marks a stopped daemon's active runs `interrupted` and keeps their worktrees ([git](git.md#crash-recovery)); their tickets stay `running`. Nothing resumes automatically after a crash: `spool run resume` continues the run, `spool run discard <ticket>` removes its worktree and branch and puts the ticket back to `ready`. Discard also works on a `blocked` ticket.

**Shutdown.** When the daemon stops, the loop cancels the timer, stops the running agents and waits up to 20 s for the workers; their runs stay `running` in the database, so the next startup marks them `interrupted` and keeps their worktrees.

## Cancel

`spool run cancel` stops the current agent (T09's cancel event) or, between agent calls, stops before the next step; then the worktree and its branch are removed (T08's teardown, marked branches only), the run becomes `cancelled` and the ticket `ready`. A paused run is cancelled at once, and its resume timer dropped.

## One run per project

A second start, while a run is running or paused, fails with

```text
a run is already active in 'demo' (T04, run 12)
```

The loop keeps a record of active runs (which also covers a paused run with no thread), and the worker thread holds `<workspace>/.spoolhq/run.lock`, an OS lock taken with the same code as the daemon's single-instance lock (`core/daemon_lock.py`: `fcntl.flock` on POSIX, `msvcrt.locking` on Windows), released when the run ends, pauses or fails, and by the OS if the process dies. A lock held by another process gives `a run is already active in 'demo' (pid 4242)`. Same-status moves are no-ops in the scheduler's table, so the lock, not the table, prevents a double start.

## `run all`

`run all` loops `next_ready()` until no ticket is ready or a ticket doesn't end `done`: blocked, paused, cancelled or held for integration.

## The integration seam

```python
class Integrator(Protocol):
    def integrate(self, ctx: RunContext) -> IntegrationResult: ...
```

`IntegrationResult.status` is `merged`, `conflict`, `gates_failed`, `failed` or `held`, with a message.

- `merged` makes the ticket and the run `done` and removes the worktree.
- `conflict` starts a `conflict_retry` attempt the first time in a run and blocks the run with the message after that.
- `gates_failed` (the gates failed on the merged code; the message is the first failing command) starts a `gate_retry` while gate retries last.
- `failed` blocks the run with the message.
- `held` puts the ticket and the run in `awaiting_approval` and keeps the worktree.

The default is `LocalIntegrator` ([integration.md](integration.md)). With `run.integration: hold` in `project.yaml`, the project gets `HoldForIntegration`, which holds every approved run:

```text
T04 approved; merge it with `spool run integrate demo T04` — worktree kept at /home/u/.spoolhq/worktrees/demo/T04
```

Tests use a fake one that returns `merged`.

## Dependencies are injected

`RunLoop(registry, projects_dir=…, worktrees_dir=…, home=…, agents=Agents(implementer, reviewer), integrator=…, clock=…, gates=…)`: tests pass `FakeRunner`s with transcript sequences, a fake clock and fake gates. The daemon builds it in its lifespan with the installed Claude Code for both roles and `LocalIntegrator`. Event bus listeners stay cheap: the loop never does real work inside a bus callback, and the resume timer only starts a worker.

## API and CLI

All routes need the token. Unknown projects, runs and tickets give 404; refusals give 409; both carry the message in `detail`. The full REST and WebSocket API is T19.

| Route | Does |
| --- | --- |
| `POST /api/projects/{name}/runs` `{"mode": "next" \| "all", "ticket": "T04" \| null}` | start a run (201, the run) |
| `POST /api/projects/{name}/runs/{id}/pause` | pause after the current step |
| `POST /api/projects/{name}/runs/{id}/resume` | resume a paused or interrupted run |
| `POST /api/projects/{name}/runs/{id}/cancel` | cancel |
| `POST /api/projects/{name}/tickets/{id}/integrate` | integrate a ticket waiting in `awaiting_approval` ([integration](integration.md#spool-run-integrate)) |
| `POST /api/projects/{name}/tickets/{id}/discard` | discard an interrupted or blocked ticket's worktree |
| `GET /api/projects/{name}/runs/current` | `active`, `working`, the active (else latest) run, its attempts, tokens and phase lines, and `last_merged` (`ticket_id`, full `commit`, `tag` of the latest finished integration, or `null`) |

```sh
spool run next <project> [<ticket>]     # start, then follow: one line per phase change
spool run all <project>
spool run pause|resume|cancel <project> [--run <id>]
spool run integrate <project> <ticket>
spool run discard <project> <ticket>
spool run status <project>              # or: no active run in 'demo'
```

With no active run, `spool run status` adds the last merged ticket once a ticket has been integrated: `last merged: T04 · 1a2b3c4 · ticket/T04` (the squash commit's first 7 hex digits and its tag).

`next`, `all`, `resume` and `integrate` poll `runs/current` once a second until no worker is on the run, and exit 1 if it ended `blocked` or `cancelled`. Ctrl-C detaches and prints `run continues in the daemon; spool run status to check`; it does not cancel.

## The real run

`tests/services/runloop/test_real_run.py` (markers `real_agent` and `integration`, skipped unless `SPOOLHQ_REAL_AGENT=1` and `claude` is logged in) runs a scratch project with one tiny ticket (`hello.py` with `hello()` and a test, its "Done when" naming the test command) through the real Claude Code for both roles, real gates and the test integrator, and prints the phase lines, the attempts and the tokens.
