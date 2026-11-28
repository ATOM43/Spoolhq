# Benchmarks

A benchmark checks what SpoolHQ builds against tests it never sees. The first one is the simulation-results dashboard (T25 sets it up, T53 runs it); its results go in `dashboard.md` here.

## Rules

1. **A benchmark lives in its own folder outside SpoolHQ's repo**, as its own local git repo with no remote (the dashboard's is `~/spoolhq-bench/dashboard/`). SpoolHQ's repo holds only the generic scoring script (`scripts/bench_score.py`), these rules and the results numbers; no spec, input, requirement, test or adapter from a benchmark.
2. **SpoolHQ's run never sees the reference or the suite.** The dogfood project gets only the benchmark's `spec/`, copied into its own repo, and agents are confined to that project's worktree.
3. **The suite is frozen before the run.** `FROZEN.txt` records the SHA-256 of `suite/` and `spec/`; the run starts with `python check_frozen.py` passing, and it is run again before scoring.
4. **An adapter only maps operations.** It turns the suite's operations (`suite/adapter_api.py`) into the app's endpoints and commands. It never changes, skips or weakens an assertion, and a missing operation fails its tests.
5. **Every run uses the same inputs**: the frozen `spec/`, nothing added or edited.

## A benchmark folder

| Path | What |
| --- | --- |
| `spec/` | The task and its inputs: exactly what the SpoolHQ project gets |
| `requirements.md` | Every requirement with an id, marked API-checkable or UI-only |
| `suite/` | Hidden pytest behaviour tests that talk to a running app over HTTP through an adapter, never importing app code; each tagged with its requirement ids (`@pytest.mark.req`); `ui-checklist.md` for the UI-only ones |
| `adapters/` | One adapter per app (`reference.py` for the hand-built one) |
| `FROZEN.txt`, `check_frozen.py` | The recorded hashes and their check |

## Scoring

```sh
just bench-score <app folder> <adapter.py> <suite folder> --out score.md
just bench-score <app> <adapter> <suite> --project <spoolhq project> --out score.md
```

`scripts/bench_score.py` copies the app folder to a temporary folder (the app itself is never written to) and runs there:

- the suite through the adapter, in the suite's own uv project (the nearest `pyproject.toml` above it), with `BENCH_ADAPTER` and `BENCH_APP` set; the result per requirement comes from the JUnit report's `req` property, and any other test property (such as a timing) is listed as a measurement;
- the app's own lint and test commands: `just lint`/`just test` or `make lint`/`make test`, or `--lint`/`--test`; and an optional `--coverage` command; the coverage is the first coverage.py `TOTAL` line;
- SpoolHQ's file-size gate over the app's git-tracked files (500 lines).

With `--project`, it also reads that SpoolHQ project's run log (`<projects_dir>/<project>/.spoolhq/state.db`, read-only): tickets run and done, first-try passes (a done ticket whose only attempt was approved), retries per ticket, review verdicts (attempt statuses `approved`, `changes_requested`, `needs_human`), blocked tickets, the user's approvals, unblocks and rejections, tokens and cost (planner runs included), and the time in runs and from the first start to the last end.

`just` splits a quoted argument at its spaces, so a `--lint`, `--test` or `--coverage` command with arguments needs the script itself: `uv run --project daemon python scripts/bench_score.py <app> <adapter> <suite> --coverage "uv run pytest --cov=app"`.
