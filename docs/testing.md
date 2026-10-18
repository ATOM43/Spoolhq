# Testing

`just test` runs every suite: pytest for the daemon, Vitest for the desktop app and `cargo test` for its Rust side. The rules for writing tests are in [CLAUDE.md](../CLAUDE.md#testing).

## Layout

| Package | Tests live in | Notes |
| --- | --- | --- |
| Daemon (`daemon/`) | `daemon/tests/<package>/test_*.py`, mirroring `src/spoolhq/` | See [Daemon test layout](#daemon-test-layout). |
| Desktop UI (`desktop/src/`) | next to the code, `*.test.ts` / `*.test.tsx` | jsdom, setup in `src/shared/lib/test-setup.ts`; Tauri calls are mocked. |
| Desktop Rust (`desktop/src-tauri/`) | `#[cfg(test)] mod tests` in the same file | Uses a temp `SPOOLHQ_HOME`. |

### Daemon test layout

```text
daemon/tests/
  conftest.py      # autouse home/projects_dir, fixtures used by more than one folder, FIXTURES_DIR
  test_layout.py   # guards this layout
  fixtures/        # shared data: ticket files, the dashboard plan, agent transcripts,
                   # context/ (prompt inputs and golden prompts in expected/)
  core/  api/  cli/
  services/
    projects/  tickets/  scheduler/  runs/
    git/           # conftest.py: wt_repo, wt_root, manager
    agents/        # conftest.py: worktree, user_home, policy; fake_claude.py
    context/       # conftest.py: fixture_inputs, assert_snapshot (SPOOLHQ_UPDATE_SNAPSHOTS=1)
    gates/         # fake_tool.py (run it with fake_tool_cmd from tests/conftest.py)
```

- **New tests go in the folder that mirrors the code they test:** `src/spoolhq/services/runs/bus.py` → `tests/services/runs/test_bus.py`, `src/spoolhq/cli/plan.py` → `tests/cli/test_plan.py`. Don't repeat the folder in the file name (`tests/cli/test_plan.py`, not `test_cli_plan.py`). Only `test_layout.py` sits directly in `tests/`.
- **Every test folder has an empty `__init__.py`**, `tests/` included, so files with the same name in different folders (`runs/test_recovery.py`, `git/test_recovery.py`) don't collide. Import shared helpers as `from tests.conftest import run_git`.
- **Fixtures live in the `conftest.py` of the only folder that uses them**; a fixture or helper used by more than one folder stays in `tests/conftest.py`. When unsure, keep it at the top.
- **Shared data stays in `tests/fixtures/`**; find it through `FIXTURES_DIR` from `tests/conftest.py`, never relative to a test file.
- **Integration tests are marked, not foldered:** `@pytest.mark.integration` wherever the test belongs.
- `tests/test_layout.py` fails on a test file directly in `tests/`, a test folder with no matching package under `src/spoolhq/`, or a test folder without `__init__.py`.

### Daemon fixtures

- `home` (autouse): points `SPOOLHQ_HOME` at a fresh tmp dir and clears every other `SPOOLHQ_*` variable, for every test. No test touches `~/.spoolhq`.
- `projects_dir` (autouse): points `SPOOLHQ_PROJECTS_DIR` at a tmp dir (not created), so no test touches `~/spoolhq-projects`.
- `git_repo`: a fresh repository with one commit on `main`, independent of the user's git config.
- `client`: a FastAPI `TestClient` for the app, with a fixed test token (`token`).
- `free_port`: an unused port on 127.0.0.1.

### Unit and integration tests

Unit tests never use the network, a real model or the real home folder. Tests that start a subprocess or are slow are marked `@pytest.mark.integration` (or `pytestmark = pytest.mark.integration` for a whole file, as in `tests/cli/test_serve.py`). `just test` and CI run both.

## Running tests

| To run… | Command |
| --- | --- |
| Everything, with coverage | `just test` |
| Daemon only | `uv run --directory daemon pytest` |
| Daemon unit tests only | `uv run --directory daemon pytest -m "not integration"` |
| Daemon integration tests only | `uv run --directory daemon pytest -m integration` |
| One daemon file or test | `uv run --directory daemon pytest tests/core/test_auth.py::test_token_is_created_once_and_reused` |
| Desktop UI only | `pnpm --dir desktop exec vitest run` |
| One desktop file | `pnpm --dir desktop exec vitest run src/entities/daemon/model/status.test.ts` |
| Desktop UI in watch mode | `pnpm --dir desktop exec vitest` |
| Desktop Rust only | `cargo test --manifest-path desktop/src-tauri/Cargo.toml --locked` |

Paths after `uv run --directory daemon` and `pnpm --dir desktop` are relative to that package.

## Coverage

- **Daemon: 85% line coverage, enforced.** `just test` runs pytest with `--cov=spoolhq --cov-report=term-missing --cov-fail-under=85`, so it (and CI) fails below the floor. The report lists the missing lines per file. Only `if TYPE_CHECKING:` blocks are excluded (`[tool.coverage.report]` in `daemon/pyproject.toml`); `# pragma: no cover` has no effect. The floor will be raised as the code grows.
- **Desktop UI: reported, no threshold yet.** `just test` runs `vitest run --coverage` (v8 provider, settings in `desktop/vitest.config.ts`) and prints a table for `src/`.

Running a single test or file with the commands above skips coverage, so the floor never fails a partial run. Add `--cov=spoolhq --cov-report=term-missing` (pytest) or `--coverage` (Vitest) to see it.

## Fake agent runner

Tests never run a real agent. `FakeRunner(transcript)` (`services/agents/fake.py`) replays a recorded Claude Code `stream-json` file behind the `AgentRunner` interface, through the same parser and callbacks as a real run, and performs the transcript's `Write` calls inside the worktree. Transcripts live in `tests/fixtures/agents/claude/` (find them through `AGENT_FIXTURES` from `tests/conftest.py`).

To test the Claude Code adapter itself, pass `fake_claude_cmd(scenario, record, *options)` as `ClaudeCliRunner(claude_cmd=…)`, with `platform="linux"` and `which=sandbox_which`: it runs `tests/services/agents/fake_claude.py`, a stand-in `claude` binary that answers `--version` and `auth status`, records its argv, environment and stdin, and prints the scenario. These tests start a subprocess, so they are marked `integration`.

One test uses the real `claude` CLI and a real model: `tests/services/agents/test_real_run.py`, marked `real_agent`. It is skipped unless `SPOOLHQ_REAL_AGENT=1` and `claude auth status` is logged in; `SPOOLHQ_RECORD=1` also saves its anonymised stream to `tests/fixtures/agents/claude/recorded/real_run.jsonl`. See [agents.md](agents.md#the-fake-runner).
