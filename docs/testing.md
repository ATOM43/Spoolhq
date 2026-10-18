# Testing

`just test` runs every suite: pytest for the daemon, Vitest for the desktop app and `cargo test` for its Rust side. The rules for writing tests are in [CLAUDE.md](../CLAUDE.md#testing).

## Layout

| Package | Tests live in | Notes |
| --- | --- | --- |
| Daemon (`daemon/`) | `daemon/tests/test_*.py` | Shared fixtures in `daemon/tests/conftest.py`. |
| Desktop UI (`desktop/src/`) | next to the code, `*.test.ts` / `*.test.tsx` | jsdom, setup in `src/shared/lib/test-setup.ts`; Tauri calls are mocked. |
| Desktop Rust (`desktop/src-tauri/`) | `#[cfg(test)] mod tests` in the same file | Uses a temp `SPOOLHQ_HOME`. |

### Daemon fixtures

- `home` (autouse): points `SPOOLHQ_HOME` at a fresh tmp dir and clears every other `SPOOLHQ_*` variable, for every test. No test touches `~/.spoolhq`.
- `projects_dir` (autouse): points `SPOOLHQ_PROJECTS_DIR` at a tmp dir (not created), so no test touches `~/spoolhq-projects`.
- `git_repo`: a fresh repository with one commit on `main`, independent of the user's git config.
- `client`: a FastAPI `TestClient` for the app, with a fixed test token (`token`).
- `free_port`: an unused port on 127.0.0.1.

### Unit and integration tests

Unit tests never use the network, a real model or the real home folder. Tests that start a subprocess or are slow are marked `@pytest.mark.integration` (or `pytestmark = pytest.mark.integration` for a whole file, as in `test_serve_integration.py`). `just test` and CI run both.

## Running tests

| To run… | Command |
| --- | --- |
| Everything, with coverage | `just test` |
| Daemon only | `uv run --directory daemon pytest` |
| Daemon unit tests only | `uv run --directory daemon pytest -m "not integration"` |
| Daemon integration tests only | `uv run --directory daemon pytest -m integration` |
| One daemon file or test | `uv run --directory daemon pytest tests/test_auth.py::test_token_is_created_once_and_reused` |
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

Placeholder: the fake agent runner arrives in T09. It will replay recorded transcripts behind the `AgentRunner` interface, so tests can drive agent runs without a real model or network. Until then, nothing in the daemon calls an agent.
