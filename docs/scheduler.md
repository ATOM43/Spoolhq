# Scheduler

The scheduler works on a project's plan as a whole: it checks that the dependency graph is sound, decides which status changes are allowed, picks the ticket that runs next and explains why none can, and computes the progress figures. Single ticket files are checked by the tickets store ([ticket-format.md](ticket-format.md)); the scheduler starts from the tickets that loaded.

The code is `services/scheduler/`. Everything in it is pure logic over a list of tickets, except `apply_transition`, which saves a status change through the tickets store.

## Plan validation

`validate_plan(tickets)` reports every problem at once. Each problem has a code, the ticket ids it is about, and a message:

| Code | Ids | Message |
| --- | --- | --- |
| `unknown_dependency` | the ticket, the missing id | `T07 depends on T99, which does not exist` |
| `cycle` | the members, in order | `cycle: T07 → T08 → T09 → T07` |
| `duplicate_id` | the id | `T04 is defined in T04-a.md and T04-b.md` |

- An arrow points in work order, as in the critical path: `T07 → T08` means T08 depends on T07.
- A cycle starts at its lowest id. Each distinct cycle is reported once. The cycles are those a depth-first walk in id order finds, so every group of tickets that depend on each other shows up; when one group has several loops, fixing the reported ones and checking again shows any that remain.
- Ids sort by number, not as strings: `T99` comes before `T100`.

**The scheduler refuses an invalid plan.** `next_ready`, `explain_idle`, `waiting_on`, `remaining_hours`, `critical_path` and `summary` raise `PlanError` (listing every problem) if `validate_plan` finds any, so nothing is scheduled from a graph with holes or loops.

## Status transitions

The table in `services/scheduler/transitions.py` (`TRANSITIONS`) is the only place that decides which status changes are allowed; a test checks that this table matches it.

| From | Allowed to |
| --- | --- |
| `draft` | `ready` |
| `ready` | `draft`, `running` |
| `running` | `ready` (cancelled or interrupted), `awaiting_approval`, `blocked`, `done` |
| `awaiting_approval` | `running` (changes requested), `blocked` (rejected or PR closed), `done` (merged) |
| `blocked` | `ready`, `running` (unblocked) |
| `done` | — (final) |

`check_transition(ticket, new_status, plan)` raises `TransitionError` for anything else:

- A move not in the table: `T07: blocked → done is not allowed; from blocked a ticket can move to ready or running` (or `…; done is final`).
- Moving to `running` also needs every dependency to be `done`: `T07 cannot start: waits for T04, T06`. This is the only rule that looks at the rest of the plan, so only it needs the plan to be valid.
- Setting the status a ticket already has is a no-op, not an error.
- An unknown status: `unknown status 'doing'; expected one of: draft, ready, running, awaiting_approval, blocked, done`.

`apply_transition(project, id, new_status)` checks the move and saves it through the tickets store, so only the `status` line of the file changes. A no-op writes nothing. Starting a ticket is refused while any ticket file of the project is invalid, since its dependencies could not all be checked.

## Next ready ticket

`next_ready(tickets)` returns the lowest-numbered ticket with status `ready` whose dependencies are all `done`, or `None`. `waiting_on(ticket, tickets)` lists the dependencies that are not done yet.

On the dashboard plan (every ticket `ready`) the order starts T01, then T02 once T01 is done (T05 also depends only on T01, but T02 is lower), then T03 once T01, T02 and T05 are done.

## Idle reasons

When `next_ready` returns `None`, `explain_idle(tickets)` says why. The first reason that applies wins:

| Code | When | Ids | Message |
| --- | --- | --- | --- |
| `all_done` | every ticket is done | none | `all tickets are done` |
| `running` | a ticket is running | the running tickets | `T04 is running` |
| `awaiting_approval` | a ticket waits for review or merge | those tickets | `waiting for approval of T04` |
| `blocked` | a ticket is blocked | the blocked tickets | `T05, T07 are blocked` |
| `waiting` | ready tickets wait for dependencies | the ready tickets; `waits_for` maps each to its unmet dependencies | `T07 waits for T04, T06` |
| `plan_not_approved` | only drafts are left | the drafts | `the plan is not approved yet: T02, T03 still in draft` |

A ready ticket can only be stuck behind a ticket that is running, awaiting approval, blocked or still a draft, so the earlier reasons name the ticket to act on; `waiting` comes up when ready tickets wait for drafts. The UI's disabled "Run next" button will show this message as its tooltip. When a ticket is ready, `explain_idle` returns `None`.

## Progress figures

- `remaining_hours(tickets)`: the sum of `estimate_h` over tickets that are not done.
- `critical_path(tickets)`: the longest chain of not-done tickets by summed `estimate_h`, in work order (each ticket depends on the one before it), with its hours. Done tickets are left out, so the path shrinks as work finishes. Of chains with equal hours, the one with the lower ids wins, compared ticket by ticket from the start, so the result is deterministic. Hours are summed as decimals, so `0.1 + 0.2` ties with `0.3`.
- `summary(tickets)`: the count of every status (zeros included), the remaining hours and the critical path.

On the dashboard plan with nothing done, 38.5 hours remain and the critical path is T01 → T02 → T04 → T07 → T08 → T11 → T12 → T15 → T16 → T17 → T18, 23 hours. T04 and T06 both take 2 hours between T02 and T07; T04 wins as the lower id.

## Commands

| Command | What it does |
| --- | --- |
| `spool plan check <project>` | Prints every plan problem and every ticket file that failed to load, or `plan is valid (N tickets)`. Exits 1 on any problem. |
| `spool plan next <project>` | The next ticket (`T02 · Backend scaffold`), or `nothing to run: <reason>`. |
| `spool plan summary <project>` | Counts per status, remaining hours and the critical path. |
| `spool tickets set-status <project> <id> <status>` | Applies a status change through the table; prints the error and exits 1 if it is not allowed. |
| `spool plan generate\|show\|approve <project>` | Drafts tickets from the spec, lists them, and moves every draft to `ready`: see [planner.md](planner.md). |

`plan next` and `plan summary` exit 1 with the problems if the plan or any ticket file is invalid. Like the other ticket commands, these read the files directly; the daemon does not need to be running.
