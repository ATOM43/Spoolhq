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
    pnpm --dir desktop exec eslint .
    pnpm --dir desktop exec prettier --check .
    pnpm --dir desktop exec tsc --noEmit
    cargo fmt --manifest-path {{ tauri_manifest }} --check
    cargo clippy --manifest-path {{ tauri_manifest }} --locked --all-targets -- -D warnings

# Run all tests.
test:
    uv run --directory daemon pytest
    pnpm --dir desktop exec vitest run
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
