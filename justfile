# SpoolHQ task runner. Run `just --list` to see recipes.
# Recipes use only plain commands with --directory/--dir/--manifest-path flags (no
# cd, &&, or shell syntax), so they run the same under sh and PowerShell.

set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

tauri_manifest := "desktop/src-tauri/Cargo.toml"

default:
    @just --list

# Install all dependencies exactly as locked.
install:
    uv sync --directory daemon --locked
    pnpm --dir desktop install --frozen-lockfile

# Lint, format-check and type-check all packages.
lint:
    uv run --directory daemon ruff check
    uv run --directory daemon ruff format --check
    uv run --directory daemon mypy
    uv run --directory daemon lint-imports
    uv run --directory daemon python ../scripts/check_line_limit.py
    uv run --directory daemon python ../scripts/check_decisions.py
    uv run --directory daemon pytest tests/api/test_openapi.py -q -p no:cacheprovider
    pnpm --dir desktop exec eslint .
    pnpm --dir desktop exec prettier --check .
    pnpm --dir desktop exec tsc --noEmit
    pnpm --dir desktop run check:api
    cargo fmt --manifest-path {{ tauri_manifest }} --check
    cargo clippy --manifest-path {{ tauri_manifest }} --locked --all-targets -- -D warnings

# Regenerate the TypeScript API client from the daemon's OpenAPI schema.
gen-api:
    uv run --directory daemon python ../scripts/dump_openapi.py ../desktop/src/shared/api/openapi.json
    pnpm --dir desktop run gen:api

# Run all tests, with coverage (the daemon fails below 85% line coverage).
test:
    uv run --directory daemon pytest --cov=spoolhq --cov-report=term-missing --cov-fail-under=85
    pnpm --dir desktop exec vitest run --coverage
    cargo test --manifest-path {{ tauri_manifest }} --locked

# Start the daemon and the desktop app together; Ctrl-C stops both.
[parallel]
dev: daemon desktop

# Start only the daemon on 127.0.0.1.
daemon:
    uv run --directory daemon spool serve

# Start only the desktop app (Vite dev server + Tauri window).
desktop:
    pnpm --dir desktop tauri dev
