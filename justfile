# SpoolHQ task runner. Run `just --list` to see recipes.
# Recipes use only plain commands with --directory/--dir/--manifest-path flags (no
# cd, &&, or shell syntax), so they run the same under sh and PowerShell.

set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

tauri_manifest := "desktop/src-tauri/Cargo.toml"

default:
    @just --list

# Install all dependencies exactly as locked.
# Also creates the empty sidecar placeholder when no binary exists, so `just lint-rust`
# works right after cloning (it never overwrites a real binary).
install: install-daemon install-desktop sidecar-placeholder

install-daemon:
    uv sync --directory daemon --locked

install-desktop:
    pnpm --dir desktop install --frozen-lockfile

# Lint, format-check and type-check all packages. CI runs the three parts as separate jobs.
lint: lint-daemon lint-desktop lint-rust

# Also runs the daemon tests that read docs/, task.md or desktop sources (a docs-only push runs only lint).
lint-daemon:
    uv run --directory daemon ruff check . ../scripts
    uv run --directory daemon ruff format --check . ../scripts
    uv run --directory daemon mypy
    uv run --directory daemon lint-imports
    uv run --directory daemon python ../scripts/check_line_limit.py
    uv run --directory daemon python ../scripts/check_decisions.py
    uv run --directory daemon pytest -q -p no:cacheprovider --no-cov tests/api/test_openapi.py tests/test_layout.py tests/services/scheduler/test_scheduler.py tests/services/projects/test_task_example.py

lint-desktop:
    pnpm --dir desktop exec eslint .
    pnpm --dir desktop exec prettier --check .
    pnpm --dir desktop exec tsc --noEmit
    pnpm --dir desktop run check:api

lint-rust:
    cargo fmt --manifest-path {{ tauri_manifest }} --check
    cargo clippy --manifest-path {{ tauri_manifest }} --locked --all-targets -- -D warnings

# Regenerate the TypeScript API client from the daemon's OpenAPI schema.
gen-api:
    uv run --directory daemon python ../scripts/dump_openapi.py ../desktop/src/shared/api/openapi.json
    pnpm --dir desktop run gen:api

# Run all tests, with coverage (the daemon fails below 85% line coverage).
test: test-daemon test-desktop test-rust

test-daemon:
    uv run --directory daemon pytest -n auto --cov=spoolhq --cov-report=term-missing:skip-covered --cov-fail-under=85

test-desktop:
    pnpm --dir desktop exec vitest run --coverage

test-rust:
    cargo test --manifest-path {{ tauri_manifest }} --locked

# Quick tests for one path while working: `just t daemon/tests/api` or `just t desktop/src/x.test.tsx`.
t path:
    {{ if path =~ '^desktop/' { "pnpm --dir desktop exec vitest run " + trim_start_match(path, "desktop/") } else { "uv run --directory daemon pytest -q --no-cov -x " + trim_start_match(path, "daemon/") } }}

# Start the daemon and the desktop app together; Ctrl-C stops both.
[parallel]
dev: daemon desktop

# No model: SPOOLHQ_DEV_FAKE_RUNNER (docs/testing.md) replays one scenario for every role.
# `just dev` with the fake runner: happy, gate-retry, review-changes, blocked or plan.
dev-fake scenario="happy":
    just _dev-with-fake-runner {{ trim_start_match(scenario, "scenario=") }}

# The `$` parameter is exported to `just dev` as the variable, under sh and PowerShell.
_dev-with-fake-runner $SPOOLHQ_DEV_FAKE_RUNNER:
    just dev

# Start only the daemon on 127.0.0.1.
daemon:
    uv run --directory daemon spool serve

# Start only the desktop app (Vite dev server + Tauri window).
desktop:
    pnpm --dir desktop tauri dev

# Build the `spool` CLI as the desktop app's sidecar binary (docs/packaging.md).
build-daemon:
    uv run --directory daemon --locked --group build python ../scripts/build_sidecar.py

# An empty sidecar file, if none exists: Tauri's build needs the file (docs/packaging.md).
sidecar-placeholder:
    uv run --no-project python scripts/build_sidecar.py --placeholder

# Set the app version in the daemon package, desktop/package.json and tauri.conf.json,
# then relock the daemon (docs/packaging.md): `just set-version 0.1.0`.
set-version version:
    uv run --no-project python scripts/release.py set-version {{ version }}
    uv lock --directory daemon

# Score an app against a benchmark (docs/benchmarks/README.md); more options with `--help`:
# `just bench-score <app> <adapter> <suite> --out score.md`.
bench-score app adapter suite *args:
    uv run --project daemon python scripts/bench_score.py {{ app }} {{ adapter }} {{ suite }} {{ args }}
