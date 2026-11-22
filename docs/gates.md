# Gates

A ticket's work must pass the project's own `install`, `lint` and `test` commands (`commands` in [`project.yaml`](project-yaml.md)) before it merges. The gates run those commands in the ticket's worktree and return structured results: a status per gate, the exit code, a trimmed excerpt of the output that keeps the first failure, and the names of the failing tests. The run loop ([run-loop.md](run-loop.md)) stores the full output in the attempt folder and feeds failures into the retry prompt ([context](context.md)); `spool gates run` runs them by hand.

The code is `services/gates/`: the results in `model.py`, command splitting and the environment in `command.py`, running one process in `process.py`, the output rules in `output.py` and `run_gates` / `check_done_when` in `runner.py`. It imports no other service package (an import-linter contract checks this); callers pass the worktree path, the commands and the timeouts in as plain values.

## What runs

`run_gates(worktree, commands, timeouts, log_dir)` runs **install → lint → test** in `worktree`:

- If install fails, times out or can't start, lint and test are `skipped`.
- Lint and test both run even if lint fails, so one retry sees every error.

Each gate gets a `GateResult`: `name`, `command`, `status`, `exit_code`, `duration_s`, `excerpt`, `failing_tests`, `output_lines`, `output_truncated` and `log_path` (`<log_dir>/<gate>.log`, or `None` if the command never ran).

| Status | Meaning |
| --- | --- |
| `passed` | Exit code 0. |
| `failed` | Any other exit code. |
| `timed_out` | The timeout passed; `exit_code` is `None`. |
| `skipped` | Install didn't pass. |
| `error` | The program wasn't found or couldn't start; `excerpt` holds the message. |

`GateRun` holds the results (in a run, the three plus the built-in [file size](#file-size), [test guard](#test-guard) and [secret scan](#secret-scan)), `passed` (all passed) and `first_failure` (the first gate that failed, timed out or errored). `to_gate_failures()` returns the failed and timed-out gates as plain dicts with the fields of T10's `GateFailure` (`command`, `exit_code`, `timed_out`, `output_excerpt`). Two runs on the same worktree give equal results apart from `duration_s`.

## File size

After install, lint and test, the run loop adds a built-in fourth gate, `file_size` ("File size" in the app's Gates panel), so a size limit holds in every project, including existing repos without a line check of their own. It is code, not a command: `check_file_sizes` in `services/gates/size.py`, given each file the ticket added, changed or renamed with its content before the ticket (the run loop's `changed_files` in `services/runloop/guards.py` reads them with git, since the gates package imports no other service). "Before" is the merge base with the default branch, so a merge of main into the ticket's branch never counts as the ticket's change.

- The limit is `gates.max_file_lines` in [`project.yaml`](project-yaml.md) (default 500; `0` turns it off and the row shows `skipped`).
- Lines are counted like SpoolHQ's own `scripts/check_line_limit.py`: `len(text.splitlines())` of the file read as UTF-8.
- A file at most at the limit passes. A longer one fails, unless it was already longer before the ticket and didn't grow: shrinking or keeping its length is fine.
- Skipped: files with a NUL byte (binary), symlinks, deleted files and anything matching `gates.max_file_lines_exempt` (default `**/*.lock`, `**/*-lock.*`, `**/*.min.*`).

Its command reads `max 500 lines per file`, and a failure lists every file, one per line:

```text
src/big.py: 612 lines, over the 500-line limit
src/old.py grew from 640 to 655 lines; it was already over the limit
```

A failure goes back to the implementer like any gate failure ("The built-in gate (max 500 lines per file) failed:" and the list in the retry prompt). A template's own line check (the `fastapi-react` justfile's `check_line_limit.py`) stays and runs as part of `lint`. `spool gates run` and the template contract check run only the three commands: the built-in gates need a ticket's diff.

## Test guard

The fifth gate, `test_guard` ("Test guard" in the app), keeps a ticket from making its tests pass by having fewer of them. It is code (`check_tests` in `services/gates/testguard.py`), given the ticket's changes against the same merge base as the file-size gate (`ticket_changes` in `services/runloop/guards.py`: every added, changed, renamed and deleted file with its content before the ticket and its added lines from `git diff -U0`). It looks only at test files, those matching `gates.test_paths` (default `**/tests/**`, `**/test_*.py`, `**/*_test.py`, `**/*.test.*`, `**/*.spec.*`). It fails when the ticket:

- deletes a test file;
- removes a test: a `def test…` in a `.py` file, or a named `it("…")` / `test("…")` (any `.skip`/`.only` suffix) in a JS/TS file, present before and gone after; a rename git detects keeps its tests, so moving a file passes;
- adds a skip or focus marker on an added line of a test file: `pytest.mark.skip` (so `skipif` too), `pytest.skip(`, `unittest.skip`, `xfail`, `xdescribe(`, `xit(`, `.skip(`, `.only(`;
- lowers coverage (below).

**Allowed:** a "Done when" item that names the exact test file (its repo path) or the exact test name allows the removal or marker. A marker belongs to the test on its line, a few lines below it (a decorator) or else the nearest one above. Ticket text can only allow; it never runs anything.

Messages name the file and test, one per line:

```text
Deleted test file backend/tests/test_old.py
Removed test test_limit_at_50hz in backend/tests/test_review.py
Added pytest.mark.skip in backend/tests/test_review.py:12 (test_limit_at_50hz)
Coverage fell from 91.2% to 88.4%
```

### Coverage

With `gates.coverage_report` set (a repo-relative path the test command writes), the guard reads the ticket's total after the test gate passes: Cobertura XML (the root tag's `line-rate`, read with a regex, never an XML parser), coverage.py's JSON (`totals.percent_covered`) or Istanbul's `coverage-summary.json` (`total.lines.pct`). A path that leaves the worktree counts as missing. The total goes into the attempt's `gates.json` as `coverage`.

Main's total lives in `<workspace>/coverage.json`. Once it has one, a configured report that is missing or unreadable **fails** the guard with `Coverage report backend/coverage.xml wasn't written; the test command must write it`: a ticket can't skip the comparison by no longer writing the file. While main has no total yet, it is skipped with a note (below). At each merge (a local or direct one, at the integration's finish, and a merged pull request, when the poller sees it), the total in the `gates.json` that landed becomes main's: the integration's gate rerun when main had moved, else the approved attempt's. The gate fails when the ticket's total is more than 0.5 points below main's. Otherwise the gate output says what happened and the gate passes:

- `Coverage 90.9% (main 91.2%)`
- `Coverage 91.2% recorded; main has none stored yet` (the first merge stores it)
- `Coverage not compared: no gates.coverage_report in project.yaml`
- `Coverage not compared: the test gate didn't pass`
- `Coverage not compared: backend/coverage.xml is missing or unreadable` (only while main has no total)

## Secret scan

The sixth gate, `secret_scan` ("Secret scan"), checks every **added** line of the ticket (`scan_secrets` in `services/gates/secrets.py`). It runs with the other gates, before review, so a hit goes back to the implementer and never reaches the reviewer's prompt or main. Patterns, first match per line:

| Name | Matches |
| --- | --- |
| `private key` | `-----BEGIN … PRIVATE KEY-----` |
| `AWS access key id` | `AKIA` or `ASIA` and 16 capitals or digits |
| `GitHub token` | `ghp_`, `gho_` or `github_pat_` and 20+ token characters |
| `Anthropic key` | `sk-ant-` and 20+ characters |
| `OpenAI-style key` | `sk-` and 20+ characters |
| `Slack token` | `xoxa-`, `xoxb-`, `xoxp-`, `xoxo-`, `xoxs-`, `xoxr-` and 10+ characters |
| `secret assignment` | a name containing `key`, `secret`, `token` or `password` (any case) assigned (`=`, `:`, `:=`) a quoted value of 16+ characters without spaces; a value starting with `/`, `~` or `.`, or holding `$ { } < >` (a path or a template), doesn't count |
| `high-entropy string` | a quoted string of 32+ characters without spaces whose Shannon entropy is above 4.5 bits per character, outside lockfiles (`**/*.lock`, `**/*-lock.*`) |

A hit reads `Possible secret in config.py:3 (Anthropic key)`, one per line (at most 50, then `… and N more`). **The value itself is never printed**: not in the gate result, `gates.json`, the retry prompt, events, logs or the app. Every pattern runs in linear time (fixed prefixes, possessive quantifiers), since the agent controls the input.

**Redaction.** The same patterns (all but `high-entropy string`) are redacted in what SpoolHQ stores, as it is written: a match becomes `[redacted: <name>]` (for a private key, each line of its body) in agent events, `transcript.jsonl`, `diff.patch`, `gates.json` and gate logs, so the Run tab, the artifact API and the event stream never show it ([runs](runs.md#redaction)). A high-entropy value is redacted only once this gate flags it, in that attempt's files and events. The worktree and the ticket branch keep the original file, so the implementer's retry (or you) can fix it; **Discard** removes both.

**Allowed:** files matching `gates.secret_scan_allow` (globs, default `[]`, for fixtures with fake keys), and any line carrying the comment `spoolhq:allow-secret`.

## No shell

A command is split with `shlex.split` (POSIX rules, so `pytest -k "adds two"` is three arguments) and run as an argument list. The program is looked up with `shutil.which` on the gate's scrubbed `PATH`. Nothing is expanded: `$HOME` or `*.py` reach the program literally.

Shell syntax is refused when `project.yaml` is validated, and again before a gate runs. Any of `&&`, `||`, `|`, `;`, `>`, `<`, `` ` `` or `$(` gives:

```text
project.yaml: commands.test: shell syntax isn't supported; put it in a justfile recipe
```

A command with an unclosed quote gives `project.yaml: commands.test: can't be split into arguments: No closing quotation`. A program that isn't on `PATH` gives the `error` status with `gate 'test': program 'just' not found on PATH`.

## Environment

Gates run code the agent wrote, so they get a scrubbed environment:

- The same allowlist as the agent ([agents](agents.md#the-environment-allowlist), in `core/agent_policy.py`): `PATH`, `HOME`, user, locale, temp, XDG, D-Bus, proxy and CA variables, and Windows' system variables.
- Never `ANTHROPIC_API_KEY`, or anything matching `*_TOKEN`, `*_KEY`, `*_SECRET` or `*_PASSWORD`, even if the allowlist ever grows to include one.
- Always `CI=1` (no watch modes or prompts), `NO_COLOR=1`, `FORCE_COLOR=0`, `PY_COLORS=0` and `TZ=UTC`.
- Stdin is closed (`/dev/null`); stdout and stderr are merged.

**Known gap: no filesystem isolation yet.** Gates run with your own file access: a test the agent wrote can read and write anything you can. The agent's own commands run in the OS sandbox ([agents](agents.md#the-sandbox-is-required)); the gates don't yet. A later ticket will sandbox them.

## Timeouts

`gates.timeouts` in `project.yaml` sets each gate's limit in seconds (each 10–7,200; defaults install 600, lint 300, test 900). When it passes, the whole process tree is stopped:

- **POSIX:** the command starts in its own session (process group); SIGTERM goes to the group, then SIGKILL after 5 s.
- **Windows:** `taskkill /T /F /PID <pid>`, as an argument list.

On POSIX, anything a command leaves running in its group after it exits is killed too. If something outside the group still holds the output pipe when the time is up, the gate counts as timed out.

## Output

- stdout and stderr are read as bytes, decoded as UTF-8 with invalid bytes replaced, ANSI escape codes stripped and `\r\n` turned into `\n`.
- The full output streams to the log file, capped at 20 MB: the line that would go over is replaced by `[output cut at 20 MB]` and `output_truncated` is set. The process is still read to the end, so it never blocks on a full pipe, and `output_lines` counts every line it printed. Nothing over the cap is kept in memory. When the log is cut, the excerpt comes from the first 20 MB.
- Passing gates have an empty excerpt and no failing tests.

### The excerpt

At most 8,000 characters, built from:

1. the first 20 lines,
2. the window around the first failure line: 30 lines before it, the line itself and as many after it as fit,
3. the last 40 lines (the summary),

in output order, never overlapping, with `[… N lines cut …]` between parts. Each part has a character budget (head 1,200, the 30 lines before the failure 1,500, the failure line 1,000, tail 3,000; the lines after the failure get the rest), so a few huge lines can't crowd out the others; a single line over its part's budget keeps its start and ends in `…`. Without a failure line the excerpt is the first 20 and the last 40 lines. Output that fits in 8,000 characters is kept unchanged.

### The first failure line

The first line matching the strongest kind present (case-sensitive), in this order:

1. pytest: `FAILED ` or `ERROR ` at the start of the line
2. `Traceback (most recent call last)`
3. Vitest / Jest: `FAIL ` at the start of the line, or a line starting with `×` or `✗` (leading spaces allowed, since both indent them)
4. `error[` (Rust), ` error TS` (TypeScript), `: error:` (compilers, mypy)
5. `error:` anywhere

So a pytest `FAILED` line wins over an earlier `error:` line.

### Failing tests

Extracted in output order, without duplicates:

- pytest: `FAILED <node id>` and `ERROR <node id>` lines; the node id runs to ` - ` or the end of the line.
- Vitest: `FAIL <file> > <test name>` lines, kept as `<file> > <test name>`.
- Anything else: none.

They become `failing_tests` in the retry prompt's previous attempt ([context](context.md)).

## "Done when" items that name a command

`check_done_when(done_when_lines, commands, run)` looks for a backticked command followed by the word `passes`, as in `` `just test` passes ``. If the backticked text exactly equals one of the configured commands, the item's status is that gate's result (`passed`, or `failed` for any other status). Anything else, such as `` `rm -rf ~` passes ``, is `not_a_gate`: it is **never run**, because ticket text is untrusted, and the reviewer judges it. Items without a backticked command followed by `passes` are left out.

## `spool gates run`

```sh
uv run --directory daemon spool gates run my-app [--path <dir>]
```

Runs the gates in `--path` (default: the project's repository, as checked out) and prints the log folder (a new temporary folder), one line per gate, then each failing gate's excerpt and failing tests:

```text
logs: /tmp/spoolhq-gates-k2j4
✓ install  just install  3.1 s
✓ lint  just lint  4.2 s
✗ test  just test  exit 1  12.8 s
```

It exits 0 when all gates pass and 1 otherwise.
