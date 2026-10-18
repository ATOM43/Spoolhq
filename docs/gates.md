# Gates

A ticket's work must pass the project's own `install`, `lint` and `test` commands (`commands` in [`project.yaml`](project-yaml.md)) before it merges. The gates run those commands in the ticket's worktree and return structured results: a status per gate, the exit code, a trimmed excerpt of the output that keeps the first failure, and the names of the failing tests. The run loop (T13) will store the full output in the attempt folder and feed failures into the retry prompt ([context](context.md)); for now `spool gates run` is the only caller.

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

`GateRun` holds the three results, `passed` (all passed) and `first_failure` (the first gate that failed, timed out or errored). `to_gate_failures()` returns the failed and timed-out gates as plain dicts with the fields of T10's `GateFailure` (`command`, `exit_code`, `timed_out`, `output_excerpt`). Two runs on the same worktree give equal results apart from `duration_s`.

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
