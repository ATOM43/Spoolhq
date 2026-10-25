# Planner

The planner turns a project's spec into draft tickets. A read-only agent reads `CONTEXT.md` (and the repository, to see what already exists) and answers with a `<plan>` JSON block; SpoolHQ validates it and writes one `draft` ticket file per ticket. You review and edit the drafts, then `spool plan approve` moves them all to `ready`. **Nothing runs until approval**: the scheduler only picks `ready` tickets.

The code is `services/planner/`: the plan schema in `model.py`, parsing and checking in `validate.py`, the prompt in `prompt.py`, draft files, hashes, re-plan merging and approval in `store.py`, and `generate_plan()` in `planner.py`. The default prompt is `services/context/prompts/planner.md.j2`. It may import `services.agents`, `services.context`, `services.projects`, `services.scheduler` and `services.tickets`, not `services.review`, `services.runs` or `services.tracker` (an import-linter contract checks this). `spool plan generate|show|approve` (in `cli/plan.py`) call it directly; the daemon runs it on a worker thread for the API (`services/runloop/planning.py`, `PlanJobs`).

## Inputs

| Input | Where from | Trusted |
| --- | --- | --- |
| The spec | `<workspace>/CONTEXT.md`; missing is an error: `no CONTEXT.md in …: write the spec there first` | no |
| A template description | `--template-description FILE` (the API's `template_description`); `None` until T16 applies templates | no |
| The kept tickets | Every ticket the plan must not touch (see [re-planning](#re-planning)), with its body | no |
| The planning rules | The prompt template | yes |
| The test command | `commands.test` in `project.yaml` | yes |

Untrusted text is only ever a variable in the sandboxed template, never template source, and sits in its own tag block (`<spec>`, `<template>`, `<kept_tickets>`) with its closing tag escaped inside it, as for the implementer ([context](context.md#untrusted-text)). A spec containing `{{ 7*7 }}` or `</spec>` renders as plain text.

Invalid ticket files stop the planner before it starts (`some ticket files are invalid; fix them first (spool plan check): …`), since it can't tell which tickets to keep.

## The agent

A fresh `claude` process with the reviewer's read-only policy (`AgentPolicy.read_only_for`): tools `Read`, `Glob` and `Grep` only, the same credential deny list, working folder the project's repository. Nothing is written by the agent, so no worktree is needed. The budget is 30 turns and, when `agents.budget_per_ticket.tokens` is set, at most that many weighted tokens over both attempts together (the planner counts as one ticket). The role is `agents.planner`, falling back to `agents.default`; only `claude-code-cli` exists for now.

## The rules (the default prompt)

- Each ticket takes 1.5 to 4 hours, with a one-line purpose, scope bullets and a testable "Done when" list.
- One ticket is one branch and one merge; every ticket adds or updates tests.
- The last "Done when" item is exactly `` `<test command>` passes ``, with `project.yaml`'s test command.
- `review_required: true` for migrations, authentication, CI, security-sensitive code or anything destructive.
- With a template, its setup counts as done and the plan starts at the real work.
- The ids to use: the kept tickets' ids are taken, the replaced drafts' ids may be reused, and new ids continue from the first number after every existing ticket.

A project can override the prompt with `<workspace>/prompts/planner.md.j2`, rendered with the same sandbox and error messages as the [implementer's](context.md#overrides). Its variables, all already escaped:

| Variable | Contents |
| --- | --- |
| `spec` | `CONTEXT.md` |
| `template` | `None`, or the template description |
| `kept` | `id`, `title`, `status`, `depends_on` (a comma-separated string), `estimate_h`, `body` |
| `reusable` | Ids of the drafts the plan replaces |
| `next_id` | The first id after every existing ticket, like `T19` |
| `test_item` | `` `just test` passes `` |
| `previous_errors` | `None`, or the list of validation errors on a retry |

## The output

The final message must end with one `<plan>…</plan>` block holding JSON; with several, the last one is used, and JSON in a code fence inside it is accepted:

```json
{
  "tickets": [
    {
      "id": "T01",
      "title": "Repository and tooling",
      "phase": 0,
      "purpose": "Set up lint, tests and CI.",
      "depends_on": [],
      "estimate_h": 1.5,
      "review_required": true,
      "scope": ["Monorepo layout with lint, format, type-check and test commands, and CI."],
      "done_when": ["`just lint` and `just test` pass in CI", "`just test` passes"]
    }
  ]
}
```

It is checked in this order, and every problem is reported at once:

1. **Schema** (Pydantic, strict, unknown keys refused): `id` is `T` and 2 or 3 digits; `phase` 0 or more; `estimate_h` from 1.5 to 4; `scope` and `done_when` non-empty; `depends_on` and `review_required` optional. Errors name the ticket: `T07: estimate_h: Input should be less than or equal to 4`.
2. **Cleaning**: `title`, `purpose` and every item become one line (whitespace runs become one space, control and format characters are removed); titles are cut to 80 characters. A title with a newline and 120 characters becomes one clean line of at most 80. An item that is empty after cleaning is an error.
3. **Ids**: unique (`T01: the id appears more than once`), not a kept ticket's (`T05: the id belongs to a kept ticket`), and either a replaced draft's id or after every existing one (`T01: new ids continue from T06`).
4. **The ticket store**: each ticket is rendered as a draft file and parsed back, so the file rules apply (`depends_on: T01 cannot depend on itself`).
5. **The whole graph**: kept tickets plus the new plan go through the scheduler's [plan validation](scheduler.md#plan-validation) (unknown dependency, cycle, duplicate id). A kept ticket that depends on a draft the new plan drops gets its own message: `T18 is kept and depends on T17, which the new plan drops`.

The "Done when" list gets `` `<test command>` passes `` appended when its last item isn't exactly that.

**Invalid output is retried once.** The retry is a fresh run with the same prompt plus a "Your previous answer was invalid:" section listing the exact errors; the previous output is never included. A second invalid answer fails with `planner output invalid: <errors>` and writes nothing. A run that doesn't complete (`usage_limited`, `max_turns`, `timed_out`, `cancelled`, `error`, `budget_exhausted`) fails with `planner run ended: <outcome>[: <error>]` and writes nothing.

## Draft files

Each ticket becomes `tickets/<id>-<slug>.md` (the slug is the branch slug of the title), status `draft`, in the [ticket format](ticket-format.md):

```markdown
---
id: T07
title: Ingestion and sync
phase: 1
depends_on: [T04, T05, T06]
status: draft
estimate_h: 3
review_required: false
---

## Purpose
Load the CSV folders into the database and keep them in sync.

## Scope
- Import CSV folders into the database and keep them in sync.

## Done when
- [ ] Re-running the import changes nothing
- [ ] A changed file updates its rows
- [ ] `just test` passes
```

The files round-trip through the tickets store byte for byte.

## Re-planning

After writing, the planner records each draft's SHA-256 in `<workspace>/.spoolhq/plan.json`:

```json
{"generated_at": "2026-10-25T09:00:00+00:00", "tickets": {"T01": "<sha256>", "T02": "<sha256>"}}
```

On the next `generate`, every ticket is sorted into one of two groups:

| Ticket | What happens |
| --- | --- |
| A draft whose file still has its recorded hash | Replaced by the new plan; deleted if the new plan doesn't have its id. |
| A draft whose file changed since (you edited it) | Kept byte for byte and given to the planner as fixed input. |
| A draft with no recorded hash (written by hand) | Kept, as above. |
| Any ticket not in `draft` (`ready`, `running`, `done`, …) | Never touched; given to the planner as fixed input. |

A missing or unreadable `plan.json` records nothing, so every draft is kept. If a kept ticket depends on a draft the new plan drops, the plan fails with a named error (and is retried once, like any invalid output).

**Writing is all-or-nothing.** Every new file (and `plan.json`) is first written as a hidden temp file next to its target; then the files being replaced or deleted are moved aside and the temp files renamed into place. Any error puts the old files back: `cannot write the plan; nothing changed: …`.

## Approval

`spool plan approve <project>` checks the whole plan again (invalid ticket files and the scheduler's plan validation) and refuses with every problem named, for example `cannot approve the plan: cycle: T01 → T02 → T03 → T01`. Otherwise it moves every draft to `ready` through the [transition table](scheduler.md#status-transitions), in one step: only the `status` line of each file changes, and the files are swapped in the same all-or-nothing way. With no drafts it says `nothing to approve` (exit 1).

## Commands

| Command | What it does |
| --- | --- |
| `spool plan generate <project> [--template-description FILE]` | Runs the planner and prints the number of drafts written with their hours, the kept and deleted tickets, the critical path and any plan problems. Exits 1 with the error if the plan fails. |
| `spool plan show <project>` | The drafts with their estimates and dependencies, the total, and the plan problems (or `none`). |
| `spool plan approve <project>` | Moves every draft to `ready`, or exits 1 naming every problem. |

They run locally; the daemon is not needed. `generate` uses your logged-in `claude`, like `spool review`.

## API

Both need the token.

| Route | What it does |
| --- | --- |
| `POST /api/projects/{name}/plan` | Body `{"template_description": null}` (optional). Checks the project, `CONTEXT.md` and the ticket files at once (404 for an unknown project, 409 for the rest), then starts the planner on the daemon's worker and returns **202** with `{"run_id", "run"}`. One plan per project at a time (409). |
| `POST /api/projects/{name}/plan/approve` | 200 `{"approved": ["T01", …]}`, or 409 with the same message as the CLI. |

The planner's work is recorded in the [run log](runs.md) as a run of kind `plan` (ticket id `plan`) with one attempt of kind `plan` in `runs/plan/<NNN>/` (its transcript) and the attempt's usage (input, output and cache-read tokens, so `spool runs show` gives the weighted total the budget counts). The run ends `done` (`18 draft tickets written`), `blocked` with the error, or `cancelled` when the daemon stops.

## Real run

`tests/services/planner/test_real_run.py` (marker `real_agent`, skipped unless `SPOOLHQ_REAL_AGENT=1` and `claude` is logged in) plans a three-paragraph spec for a small CLI tool and checks the plan validates. On 2026-10-25 it took one call: 19,138 input tokens (15,506 of them cache reads) and 3,414 output, 8,596 weighted, for six tickets.

## Known limits

- **The spec isn't trimmed.** The whole `CONTEXT.md` goes into the prompt; a very large spec costs tokens on every turn.
- **Only `claude-code-cli` runs the planner.** `agents.planner` accepts the other backend names, but they don't exist yet.
- **Ids are not renumbered.** A plan with an id below the next free one is retried, not fixed.
