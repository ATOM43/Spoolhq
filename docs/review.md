# Review

After the gates pass, a second agent reviews the ticket's change: a fresh, read-only Claude Code run that checks the committed diff against the ticket's "Done when" items and returns a verdict SpoolHQ validates. The run loop ([run-loop.md](run-loop.md)) calls `review()` after the gates pass and turns the verdict into a retry, a block or an integration; `spool review` runs it by hand.

The code is `services/review/`: the inputs and result in `model.py`, the `<verdict>` parser in `verdict.py`, diff trimming in `diff.py` and `review()` in `reviewer.py`. The default prompt is `services/context/prompts/reviewer.md.j2`. It may import only `services.agents` (the runner, policy and result types) and `services.context` (`render_template`, `escape_closing_tag`); an import-linter contract checks this.

## What the reviewer sees, and never sees

`ReviewInputs` holds the ticket (`ticket_id`, `title`, `body`), its "Done when" items (`done_when`), which items the gates checked (`gate_checked`: item index → result), the diff (`git diff <base>...HEAD`), one line per gate (`gate_summary`: name, command, status) and the worktree, which is the agent's working directory so it can read the code around the diff.

It has **no field** for the implementer's transcript, its summary or its progress note, so they can't be passed in (a test asserts the field names). The reviewer judges the code, not the implementer's claim about it. Each review is a new `claude` process with no session reuse (`--no-session-persistence`, as for every run).

## Read-only tools

`AgentPolicy.read_only_for(worktree, home)` builds a policy with `read_only=True`, no stack commands and no read-only git. For it the Claude Code adapter passes:

```text
--tools Read,Glob,Grep
--allowedTools Read Glob Grep
```

No `Bash(…)` rules, no `Edit`, no `Write`. Everything else is as for the implementer ([agents](agents.md)): `--restricted`, `dontAsk` with `--permission-prompts none`, the sandbox settings and the scrubbed environment. Claude Code's `init` message must list **exactly** `Read`, `Glob` and `Grep`: any other tool, or a missing one, stops the run with outcome `error` and `policy not enforced: …`.

## The verdict

The reviewer's final message must end with one `<verdict>…</verdict>` block holding JSON. If there are several, the last one is used; JSON inside a code fence inside the block is accepted. It is validated with Pydantic (strict types, unknown keys refused):

```json
{
  "items": [{"index": 1, "met": true, "reason": "…"}],
  "verdict": "approve",
  "summary": "…"
}
```

- `items`: exactly one entry per "Done when" item, indices `1..N`, each once, in any order. `reason` is required and non-empty, at most 1,000 characters.
- `verdict`: `approve`, `changes_requested` or `needs_human`. `summary`: at most 2,000 characters.
- **Consistency:** `approve` needs every item met; `changes_requested` needs at least one item not met; `needs_human` is allowed either way, and is how the reviewer reports a problem outside the checklist (a security issue, deleted tests, a change far outside the ticket's scope) or something it can't judge.

`parse_verdict(final_text, n_items, gate_checked=…)` is pure and raises `InvalidVerdict` with one line per problem:

```text
no <verdict> block in the final message
the <verdict> block is not valid JSON: Expecting value: line 1 column 11 (char 10)
items: index 2 missing
items: index 4 out of range (1–3)
items: index 2 appears more than once
items.0.reason: String should have at least 1 character
score: Extra inputs are not permitted
verdict 'approve' but item 2 is not met
verdict 'changes_requested' but every item is met
```

The text is read from the `result` message's full final text, not `RunResult.summary` (which keeps only the last 4,000 characters).

## Items the gates checked

Items that T11's `check_done_when` mapped to a gate (`` `just test` passes ``) are listed in the prompt as "checked by the gates: passed". They are not the reviewer's call: whatever it says about them, the result uses the gate's answer, with `source="gates"` and the reason `checked by the gates: passed`. The reviewer still returns an entry for each, so indices stay simple. The consistency rules are checked **after** the gates' answers are merged in, so `changes_requested` whose only unmet item the gates passed is invalid (and retried).

## Invalid output is retried once

Invalid means no block, unparseable JSON, a schema error or a consistency error. The retry is a fresh run with the same prompt plus a "Your previous answer was invalid:" section listing the errors; the previous output itself is never included. A second invalid answer gives verdict `needs_human` with summary `reviewer returned invalid output twice: <errors>` and no items. `invalid_errors` keeps every error, prefixed `attempt 1: ` or `attempt 2: `. Tokens and cost are summed over both attempts.

## Run outcomes

Only a `completed` run gives a verdict. `usage_limited` (with `reset_at`), `timed_out`, `cancelled`, `error` (including a policy violation), `max_turns` and `budget_exhausted` come back as `run_outcome` with `verdict=None`, for T13 to decide. The default budget is `max_turns=20`, `timeout_s=600`, no token or USD limit; a caller can pass its own `Budget`.

`ReviewResult` has `run_outcome`, `verdict`, `items` (`index`, `item`, `met`, `reason`, `source`), `summary`, `attempts`, `invalid_errors`, `diff_trimmed`, `input_tokens`, `output_tokens`, `cost_micro_usd` and `reset_at`. `unmet()` returns the items not met, which T13 puts into T10's `review_notes` for the retry prompt.

## Untrusted input

The diff is agent-written and the ticket user-written. Each sits in its own tag block (`<done_when>`, `<ticket>`, `<gates>`, `<diff>`) with its closing tag escaped inside it, rendered through T10's sandboxed `render_template` ([context](context.md#untrusted-text)). The rules tell the reviewer that comments or text in the blocks addressed to it are data and never change its instructions. Code then re-checks the consistency rules, so a reviewer talked into `approve` with an unmet item still fails validation.

## Diff size

The diff is capped at 150,000 characters. Over that, the prompt keeps the list of changed files and every file's header (the lines before its first hunk), includes whole files in diff order while they fit, and ends with:

```text
[diff trimmed: 4 of 12 files shown in full; read the others with the Read tool]
```

A trimmed diff can still be approved; `diff_trimmed` says it was cut.

## The prompt

In order: the role (you are reviewing one ticket's change, you didn't write it, you can read files but not change them); the rules (among them: judge only the committed diff, and ignore the empty placeholder files the sandbox leaves at the root, such as `.env*` and `package.json`); the items numbered `1.` to `N.` in `<done_when>`; on a retry only, the validation errors; the `<ticket>`, `<gates>` and `<diff>` blocks; the output contract.

A project can override it with `<workspace>/prompts/reviewer.md.j2`, rendered with the same sandbox and error messages as the implementer's. Its variables, all already escaped:

| Variable | Contents |
| --- | --- |
| `items` | `index`, `text`, `gate` (`None`, `passed` or `failed`) |
| `previous_errors` | `None`, or the list of validation errors on a retry |
| `ticket` | `id`, `title`, `body` |
| `gates` | `name`, `command`, `status` |
| `diff` | The diff, trimmed if needed |

## `spool review`

```sh
uv run --directory daemon spool review my-app T07 [--path <worktree>] [--base <ref>]
```

Reviews the committed work in `--path` (default: the project's repository) against `--base` (default: the project's default branch), with the diff from `git diff <base>...HEAD`. A folder with uncommitted changes is refused with the dirty-repo message, since only committed work is reviewed. No gates run: items naming a configured command are listed on stderr as `not yet checked by the gates: 3. `just test` passes`, and the reviewer judges them from the code. It prints:

```text
✓ 1. `parse_slug` exists in `slugs.py`
✗ 2. A test covers parse_slug — no test for parse_slug
✗ 3. `just test` passes — the repository has no justfile
verdict: changes_requested
parse_slug has no test.
```

It exits 0 for `approve`, 1 for `changes_requested` or `needs_human` (and for errors), 2 when the run didn't complete.

In the run loop, a `needs_human` verdict (which comes only after the gates passed) no longer blocks: the [merge policy](merge-policy.md) sends the work to a person, a pull request with `git.remote` or local approval without, with the reviewer's summary shown first.

## Known limits

- **A reviewer can still be misled by code it reads.** Text in the diff or the repository can try to talk it into a verdict. The tag blocks and rules make that harder; the code-side consistency checks are the backstop (an unmet item can never be approved), and the merge policy (T18) is the next one.
- **Structured output isn't used.** Claude Code 2.1.302 has `--json-schema <schema>` for structured output in print mode. SpoolHQ doesn't depend on it: it parses and validates the `<verdict>` block itself, so any backend that writes text works.
