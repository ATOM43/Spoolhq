# Decisions

Each entry is one decision and the reason for it. Add new entries at the bottom; to change one, add a new entry that supersedes it.

1. **Name: SpoolHQ** (Python package `spoolhq`, CLI `spool`). A spool feeds thread one turn at a time, as the loop feeds tickets; `spoolhq` was free as a package name and `spool` is short to type.
2. **UI: Tauri 2 + React + TypeScript.** Small native binaries on all three desktop platforms, with a mainstream, well-typed UI stack.
3. **Separate Python daemon (FastAPI).** Runs must survive closing the window, and the same daemon can run headless on a server.
4. **CLI: Typer.** Typed, minimal-boilerplate CLI that shares code and types with the daemon.
5. **Agent runtime: Claude Agent SDK behind an `AgentRunner` interface.** Use the best-supported coding agent now, without locking out other agents later.
6. **Storage: files for projects and tickets, SQLite for run history.** Specs and tickets stay readable and diffable in git; run history needs queries, not diffs.
7. **Stack templates: Copier.** It can both generate and later update projects from a template, which plain cookiecutter cannot.
8. **Only the planner, implementer and reviewer are LLM agents; everything else is plain code.** Gates, git, merging and tracker sync must be deterministic and testable.
9. **Local git first, GitHub optional.** The tool must work offline and without an account; GitHub adds pull requests on top.
10. **Licence: Apache-2.0.** Permissive, with an explicit patent grant, and compatible with the prior art we may borrow from.
