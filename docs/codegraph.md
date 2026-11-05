# Code graph

Most of an agent's steps go into exploring the repository (the T29 token study). To cut that, the implementer's and the planner's prompts carry a short **code map**: the summary of a [Graphify](https://github.com/Graphify-Labs/graphify) graph of the code. It lists the most connected symbols, surprising connections, import cycles and groups of related symbols. The code is in `services/codegraph/` (it imports no other service; plain paths in, text out), and the wiring is in `services/runloop/prompting.py` and the context pack ([context](context.md)).

## Graphify is optional

Graphify is an external tool (`uv tool install graphifyy==0.9.92`), not a dependency. SpoolHQ is tested with **0.9.92**.

- If `graphify` isn't on `PATH`, or `graphify --version` doesn't print a version, runs carry on without a map and log one note: `no code map: graphify is not on PATH or its version can't be read`.
- A different version works but logs a warning, and `spool agents` shows it:

  ```text
  graphify
    installed  yes (0.9.92)
  ```

- If a build fails or takes more than 120 s, the run carries on without a map. The run doesn't call Graphify again for later attempts, so a hanging Graphify costs at most one timeout per run.

## Offline only

Graphify always runs with `GRAPHIFY_BACKEND=none` and `extract --code-only`: a local AST pass, no LLM, no network. It gets the same allowlisted environment as the agents ([agents](agents.md#the-environment-allowlist)), so no API key reaches it. Every call is an argument list with a 120 s timeout, and on a timeout the whole process tree is stopped. Graphify's own Claude Code skill, MCP server and git hooks are never installed.

## When it runs

- **Implementer**: in the run's worktree, after the worktree is created and before the first attempt. Before a retry it runs again only if the code changed: the worktree's `HEAD` moved (the last attempt committed something) or there are uncommitted changes (a merge being resolved). A retry with the same code reuses the map.
- **Planner**: on the project's checkout, read-only, before the plan run starts.

## The cache

Graphify keeps a content-hash cache (`graphify-out/cache/ast/v<version>-…/`, plus `manifest.json`). A later `extract` against the same output folder re-processes only the files whose content changed, even from a different checkout path. SpoolHQ keeps that cache once per project, outside the repository:

```text
<workspace>/.spoolhq/codegraph/
  lock              an OS file lock while a refresh runs
  current.json      {"build": "b-<id>", "version": "0.9.92"}
  b-<id>/graphify-out/  the current build: cache/, manifest.json, graph.json, GRAPH_REPORT.md
```

What Graphify 0.9.92 offers, checked with `--help` and by running it:

- `graphify extract <path> --out DIR` writes everything to `DIR/graphify-out/`, cache included, and nothing into `<path>`. So SpoolHQ points Graphify at its cache instead of copying a cache into the worktree.
- `graphify update <path>` has no `--out`; it writes to `<path>/graphify-out/`. SpoolHQ doesn't use it. An incremental `extract` does the same job.
- `graphify cluster-only DIR --no-label --no-viz` writes `DIR/graphify-out/GRAPH_REPORT.md` and no `graph.html`.

A refresh:

1. Takes the cache's file lock. If another run holds it, the refresh gives no map instead of waiting.
2. Reads `current.json`. If it was written by another Graphify version, it deletes the whole cache.
3. With a current build, copies it to `tmp-<id>/` and runs `graphify extract <checkout> --code-only --out tmp-<id>`: an **update**, which re-processes only changed files. Without one, it runs the same command into an empty folder with `--force`: a **full build**.
4. Runs `graphify cluster-only tmp-<id> --no-label --no-viz` for the report.
5. Saves the build atomically: it renames `tmp-<id>` to `b-<id>`, writes the new pointer to a temp file and `os.replace`s it over `current.json`, then deletes the old build. A crash at any step leaves the previous pointer and build untouched, and leftovers are deleted on the next refresh.

If an update fails, SpoolHQ deletes the cache and does one full build. If that fails too, it logs the error and the run carries on without a map.

## Never committed by SpoolHQ

The cache lives in the workspace, never in the repository. Graphify runs from the cache folder with `--out` there, so it writes nothing into the worktree. If an agent creates an untracked `graphify-out/` anyway, the integrator's diff guard drops it as build junk ([integration](integration.md)). A project that commits its own graph (SpoolHQ's own repository does) keeps it: files under `graphify-out/` that the default branch already tracks are committed like any other change, and the run log names them. SpoolHQ never adds a graph a project doesn't track.

`spool prompt show` doesn't run Graphify, since that would build the cache. It ends its stderr notes with `Code map: not included here (built only during runs).` (left out when `context.code_map_chars` is 0).

## In the prompt

From `GRAPH_REPORT.md`, the prompt keeps the Summary, God Nodes, Surprising Connections, Import Cycles and Communities sections. It leaves out the title (it names SpoolHQ's temp folder), the build commit, the list of placeholder community names, knowledge gaps and suggested questions (which tell the reader to run Graphify).

The map is its own `<code_map>` block under "Code map", after the notes. Its text is untrusted: it is escaped and fenced like the other blocks ([context](context.md#untrusted-text)). It is capped at `context.code_map_chars` (default 8,000; `0` turns the map off and Graphify is never run) and counts against `context.max_chars`. It is filled last, so the notes come first. When it is too long, the least connected communities (fewest `Nodes (N)`) are dropped first, and a note says how many were kept (`[trimmed: kept the 40 most connected of 161 parts]`). The reviewer never gets the map. Every backend gets it the same way, as part of the prompt.

## AI labels later

The communities are named `Community 0`, `Community 1`, … because the report is built with `--no-label`. Graphify can name them, and add semantic edges from docs, with an LLM (`graphify extract` without `--code-only`, `graphify label`, a `--backend`). SpoolHQ doesn't do that yet. A later switch would:

- set a backend and pass its key to Graphify only (today's environment has no keys);
- drop `--code-only` and `--no-label`;
- rely on the per-project cache. Graphify's semantic cache is keyed by file content like the AST cache, so each run pays for the files that changed since the last run, not for the whole repository. That is why the cache lives per project and survives runs.

## SpoolHQ's own graph

This repository commits a graph in `graphify-out/` for agent context. Read `graphify-out/GRAPH_REPORT.md` before starting work; the graph can be stale, so trust the code when they disagree. If Graphify is installed, `graphify query` and `graphify path` may be used read-only.

After a ticket's code is final and `just lint && just test` pass, rebuild it offline (install with `uv tool install graphifyy==0.9.92` if it's missing):

```sh
GRAPHIFY_BACKEND=none graphify extract . --code-only
graphify cluster-only . --no-label
```

Commit the updated `graphify-out/` files in the same commit as the ticket, never `graphify-out/graph.html`. If Graphify fails, don't block the ticket: say so in the report.
