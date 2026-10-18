# SpoolHQ task runner. Run `just --list` to see recipes.
# Recipes use only plain commands with --directory/--dir flags (no cd, &&,
# or shell syntax), so they run the same under sh and PowerShell.

set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

default:
    @just --list

# Install all dependencies exactly as locked.
install:
    uv sync --directory daemon --locked
    pnpm --dir desktop install --frozen-lockfile

# Lint, format-check and type-check both packages.
lint:
    uv run --directory daemon ruff check
    uv run --directory daemon ruff format --check
    uv run --directory daemon mypy
    pnpm --dir desktop exec eslint .
    pnpm --dir desktop exec prettier --check .
    pnpm --dir desktop exec tsc --noEmit

# Run all tests.
test:
    uv run --directory daemon pytest
    pnpm --dir desktop exec vitest run

# Start the daemon on 127.0.0.1 (the desktop app arrives in T03).
dev:
    uv run --directory daemon spool serve
