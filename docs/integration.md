# Integration

When the reviewer approves a ticket, SpoolHQ turns the run's branch into **one commit on the local default branch**, tagged `ticket/<id>`, with the ticket's progress entry and decisions written to the [notes files](#notes-files). With `git.remote` set, the commit is pushed to GitHub before `main` moves, or opened as a pull request: see [GitHub delivery](github.md).

The code is in two parts. The git mechanics are `services/git/integrate.py`: plain values in, no other service. The orchestration is `services/runloop/integration.py`: `LocalIntegrator`, the journal, the gates rerun, the conflict hand-off and recovery. The journal table and its API live in `services/runs/journal.py`.

## The steps

For an approved run of T04, with `main` as the default branch:

1. **Check the main checkout.** If `main` is checked out there, it must be clean, with no rebase or merge in progress. If it isn't, integration waits (see [A dirty main checkout](#a-dirty-main-checkout)). If the tag `ticket/T04` already exists, the run is blocked: `tag ticket/T04 already exists; delete it or rename the ticket`.
2. **Journal: `merging`**, with `main_sha`, the commit `main` points at now.
3. **Merge main into the worktree:** `git merge --no-ff --no-commit main` in the run's worktree.
   - A conflict goes back to the implementer (see [Conflicts](#conflicts)).
   - If main had nothing new, there is nothing to merge, and the gates are not rerun: the approved attempt already ran them on this exact tree.
   - Otherwise SpoolHQ concludes the merge with a commit on the run branch and **reruns the gates** in the worktree. Their results and logs replace the approved attempt's `gates.json` and gate logs, which the retry prompt reads. A failure there starts a `gate_retry` attempt, counted against `limits.gate_retries` like any other.
4. **Build the squash commit** in the worktree: detach `HEAD` at the branch tip, `git reset --soft <main_sha>`, apply the [diff guard](#the-diff-guard), ask the [merge policy](merge-policy.md) (its rules include [new dependencies](merge-policy.md#new-dependencies): a name the squash adds to `pyproject.toml`, `package.json`, `Cargo.toml` or a `requirements*.txt` needs a person unless `merge_policy.new_dependencies` is `allow`; a ticket that needs a person stops here: the worktree goes back to its branch and the ticket waits for `spool run approve`), append the `PROGRESS.md` entry and commit. The commit's only parent is `main_sha`. Its tree is the branch tip, minus build junk, plus the entry. The run branch doesn't move, so a retry starts from the same work. **Journal: `committed`**, with the commit's sha.
5. **Advance main.** This is compare-and-swap: it succeeds only if `main` still points at `main_sha`.
   - `main` checked out: it must still be clean and its `HEAD` must be `main_sha`, then `git merge --ff-only <commit>` there.
   - Otherwise: `git update-ref refs/heads/main <commit> <main_sha>`, which fails if `main` moved.
   - If `main` moved, the worktree goes back to its branch and integration starts over at step 1. After 3 tries the run is blocked: `main kept moving during integration`.
   - **Journal: `advanced`.**
6. **Tag** `ticket/T04`, lightweight. **Journal: `tagged`.**
7. **Finish:** the coverage total in the landed `gates.json` (the rerun's, or the approved attempt's) becomes main's in `<workspace>/coverage.json` ([coverage](gates.md#coverage)); the ticket and the run are `done`, the worktree and its branch are torn down, the event `integrate` records `{"commit", "tag"}`, and the run prints `T04 · integrate · merged 3f2a9c1 · ticket/T04`. **Journal: `done`.**

Each journal state is committed to `state.db` in its own transaction before the next step starts.

### Why main is only fast-forwarded

All history work (the merge, conflict resolution, the squash) happens in the run's worktree, which SpoolHQ owns. The user's main checkout only ever sees `merge --ff-only`, `update-ref` and `git tag`. SpoolHQ never rebases, resets, stashes, checks out or cleans there. A conflict, a crash or a failed check can leave the worktree in a mid-merge state, but never `main`.

Merging main into the branch replaces the plan's "rebase onto main". The result is squashed into one commit anyway, so a merge and a rebase give the same tree, and only the merge leaves a conflict in the worktree rather than in the middle of a rewritten history.

### The commit

```text
T04: Project workspace and settings

Added the project workspace and project.yaml validation, with errors
for every bad field.

SpoolHQ-Ticket: T04
SpoolHQ-Run: 12
```

- **Subject:** `T04: <title>`, at most 72 characters. The title is untrusted, so whitespace and control characters (newlines, tabs, escape sequences) become single spaces before it is cut.
- **Body:** the progress entry of the implementer's run note, wrapped at 72 characters.
- **Trailers:** `SpoolHQ-Ticket` and `SpoolHQ-Run`.
- The message is passed as one argument. Author and committer come from the user's git config, with `user.useConfigOnly=true`; hooks and signing are disabled as for every SpoolHQ git call ([git](git.md#hooks-and-signing)).

## Notes files

SpoolHQ is the only writer of a project's notes files: `PROGRESS.md`, `docs/progress-archive.md`, `DECISIONS.md` and `docs/decisions/*.md`. The implementer hands its progress entry and decisions back in its [run note](context.md#the-run-note); the squash commit writes them, under the project's run lock, after the merge policy decided (so they don't count toward the diff size). Everything outside what SpoolHQ adds keeps its bytes, and files are read and written as bytes, so line endings and undecodable bytes survive. `CLAUDE.md` is never written. The code is `services/notes/` (`write_notes`, `notes_problems`), which imports no other service.

**PROGRESS.md.** The newest entries sit between two marker lines, newest first:

```markdown
<!-- spoolhq:recent:start -->

### T07 · Parse slugs (2026-11-20)

Added slug parsing.

### T06 · … (2026-11-19)

…

<!-- spoolhq:recent:end -->
```

The new entry goes at the top. The newest 5 stay; older ones move, word for word, to the end of `docs/progress-archive.md` (created with a heading when missing), oldest first. Text inside the markers before the first `### ` entry is kept. A file without the markers gets them at its end on the first merge, everything above untouched; a missing file is created with a `# Progress` heading. A file with only one marker, two of either, or the end before the start blocks the ticket ("The notes files don't match: PROGRESS.md needs exactly one spoolhq:recent start and end marker"). Code never rewrites anything outside the markers.

**Decisions** (the split layout): each decision is appended to `docs/decisions/<area>.md` (created with `# Decisions · <area>`) in the format the [context pack](context.md#a-split-decisionsmd) reads, and its index line to `DECISIONS.md`:

```markdown
012. Routes are plural
    Like the rest of the API.

012 · Routes are plural · docs/decisions/api.md
```

`NNN` is one more than the highest number in the index, three digits. Without decisions, an existing `DECISIONS.md` isn't touched; a missing one is created with a `# Decisions` heading.

**Converting old flat notes.** Before writing, every merge runs `convert_notes` (`services/notes/convert.py`); it changes something only in a project still in the old flat layout, so in practice on its first merge, in the same commit:

- `PROGRESS.md` without the markers keeps everything; the markers are added at its end (above), and the entries already in the file stay above them, untouched.
- A `DECISIONS.md` with no index lines but entries is split. An entry starts at the left margin with `N. ` (numbered) or `- ` / `* ` (unnumbered) and goes on with indented or blank lines; the text before the first entry is its intro. Every entry moves, word for word, to the end of `docs/decisions/general.md` (created with `# Decisions · general`) as `NNN. <rest of its first line>` with its other lines unchanged, keeping its number; unnumbered ones get the numbers after the highest, in order of appearance. `DECISIONS.md` keeps its intro and becomes the index: `NNN · <title> · docs/decisions/general.md`, the title being the bold part of the first line (`1. **Plain SQL**: no ORM.` → `Plain SQL`) or the whole line.
- A file that can't be split blocks the ticket and changes nothing: "DECISIONS.md couldn't be converted: line 12 isn't part of an entry: ## Later" (a line at the margin after the first entry that isn't one), "… entry 3 appears more than once" or "… line 4 is an entry without a title".
- The squash commit's body lists what was converted, before the trailers: `- PROGRESS.md: added the spoolhq:recent markers at the end`, `- DECISIONS.md: moved 4 entries word for word to docs/decisions/general.md; DECISIONS.md is now the index`.

A `DECISIONS.md` with index lines, or with only a heading and intro, is already in the split layout and isn't touched; so a hand-written intro must not start lines with `N. `, `- ` or `* `. The notes check below runs after the conversion, so numbers with a gap block the ticket with its usual message.

**The notes check.** Before the commit, `notes_problems` compares the index with the area files: every index line has exactly one entry in `docs/decisions/*.md` and the reverse, numbers run 1..N without gaps or duplicates, each line names the file its entry is in, and each title is its entry's heading (`N. title`, or the bold part of `N. **title** …`). A `DECISIONS.md` without index lines passes. The first problem blocks the ticket: "The notes files don't match: DECISIONS.md: 2 is missing". A notes file that resolves outside the repository (a symlink) is refused the same way.

**Agents can't edit them.** After each attempt's commit, a branch that adds, changes, deletes or renames a notes file fails the `policy` step with "The agent edited notes files: <file>; put progress and decisions in the run note instead". Unlike [planted agent settings](agents.md#repo-safety), this is not a security issue, so it goes back to the agent as a gate retry. The diff runs from the merge base with the newest commit on the branch that no attempt made (SpoolHQ's squash on a pull request branch, a merge of main), or the branch's base: main or SpoolHQ changing the notes meanwhile never counts.

## Conflicts

When the merge in step 3 conflicts, the worktree is left mid-merge with its conflict markers, and the run starts an implementer attempt of kind `conflict_retry`. Its prompt lists the conflicting files ("Files with conflicts") and, under "Note from SpoolHQ", says to resolve every marker and keep the intent of both sides.

After that attempt, SpoolHQ stages everything and checks two things: `git ls-files -u` is empty, and no conflicting file has a line that is a conflict marker (a line `=======`, or one starting `<<<<<<<` or `>>>>>>>` followed by a space or nothing else). It then concludes the merge, and the run continues at the gates and then the reviewer. Review retries count as usual.

The run is blocked with `merge conflict with main in: <files>` if:

- markers are left behind or files are still unmerged, or
- a second conflict happens in the same run (main moved again and conflicts again).

T42's agent-settings check runs again after the conflict retry's commit, before the gates. It compares against the main that was merged in (the conflict sets the worktree's base to it), so settings main changed don't count as the agent's, while settings the agent writes while resolving block the ticket with "The agent changed agent settings: <files>". A settings change that reaches main during the retry is merged in at integration, as main's own.

## The diff guard

Before the squash commit, every file in `git diff --cached --name-only <main_sha>` is checked. Names are matched case-insensitively.

- **Build junk is left out** of the commit and listed in the run log, as a `log` event with the files and a phase line. The files stay on disk in the worktree; nothing in the main checkout is deleted. Junk is any path through a folder named `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `node_modules/`, `*.egg-info/`, `.pnpm-store/`, `.npm/` or `graphify-out/` (a Graphify graph; SpoolHQ keeps its own outside the repository, see [code graph](codegraph.md)), or through `.yarn/cache/`, and any file named `*.pyc` or `.DS_Store`. A junk path the default branch already tracks (a project that commits its own `graphify-out/`, say) is not junk: its change is committed, and an info `log` event (`tracked files in build folders kept in the commit`) names it.
- **Likely secrets block the ticket**, for a person to look at; nothing is retried. These are `.env` and `.env.*` (but not `.env.example`), `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa*`, `id_ed25519*`, `.netrc`, `.npmrc`, `.pypirc`, `credentials.json`, `*.keystore`, and anything under `.ssh/` or `.claude/`. The message is `refusing to commit likely secrets: <files>`.
- **A symlink that points outside the repo blocks**: any added or changed symlink whose target is absolute or, resolved from the link's folder, leaves the repository. The message is `refusing to commit a symlink that points outside the repo: <path> -> <target>`. Symlinks within the repo are allowed. Modes and targets are read from the index, so this works where git checks symlinks out as plain files (Windows). Junk is dropped first, so a link inside `.pnpm-store/` is simply left out.
- **Any added or changed file over 5 MB blocks** (MB = 1,048,576 bytes): `file too large to commit: <file> (12.3 MB)`.

A block here puts the worktree back on its branch, so the work can be inspected as it was.

## A dirty main checkout

**A dirty main checkout never blocks the ticket; integration waits.** If `main` is checked out and has uncommitted changes or untracked files, the ticket and the run stay in `awaiting_approval` with:

```text
main checkout has uncommitted changes in /home/u/code/x; commit or stash them, then run spool run integrate demo T04
```

SpoolHQ touches nothing there. Once the checkout is clean, `spool run integrate demo T04` merges. A rebase or merge in progress in the main checkout waits the same way. If `main` isn't checked out (another branch is), the checkout's state doesn't matter, because `update-ref` never touches the working copy.

## Crash recovery

At daemon startup, after the run log marks the stopped daemon's runs `interrupted` and before worktree recovery ([git](git.md#crash-recovery)), every open journal row (`merging`, `committed`, `pushed`, `advanced` or `tagged`) is checked (a project with `git.remote` asks the remote first: [GitHub delivery](github.md#crash-recovery)):

| Found | Recovery |
| --- | --- |
| `main` is at (or past) the squash commit | The advance happened. Finish: tag, ticket and run `done`, worktree and branch removed, event `integrate`, journal `done`. |
| `main` hasn't reached it, and the main checkout is clean (or `main` isn't checked out) | The worktree goes back to its branch (`git merge --abort` if needed). Ticket and run go to `awaiting_approval`: `integration interrupted; run spool run integrate <project> <ticket>`. |
| `main` hasn't reached it, and the main checkout is dirty (a fast-forward cut off mid-checkout looks like this) | The checkout is not touched. Ticket and run go to `awaiting_approval`: `integration interrupted while updating <repo>; check git status there before retrying`. |
| A rebase or merge is in progress in the main checkout | Nothing is done. The row is reported and stays open for the next startup. |

Every step is safe to repeat, and a recovered row is closed, so running recovery twice changes nothing. A row whose integration stopped before `main` moved (a conflict, failing gates, a block or a wait) is closed as `abandoned` when it stops, so recovery never sees it.

### The journal (schema version 3; T17 adds two states)

```sql
CREATE TABLE integrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    ticket_id TEXT NOT NULL,
    default_branch TEXT NOT NULL,
    main_sha TEXT NOT NULL,          -- main when the integration started
    commit_sha TEXT,                 -- the squash commit, from `committed` on
    state TEXT NOT NULL,             -- merging | committed | pushed | advanced | tagged | done | abandoned | pr_open
    started_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

`pushed` (T17) means the remote has the commit; `pr_open` closes a row delivered as a pull request until it is merged (`done`) or closed (`abandoned`). `start_integration`, `set_integration_state`, `get_integration` and `open_integrations` are in `services/runs/journal.py`.

## `spool run approve` (`spool run integrate`)

```sh
spool run approve <project> <ticket>     # spool run integrate is an alias
```

This integrates a ticket that waits in `awaiting_approval` with its worktree: one the [merge policy](merge-policy.md#local-approval) held for you (hold mode included), or one held by a dirty checkout or an interrupted integration. It calls `POST /api/projects/{name}/tickets/{id}/approve`, which continues the ticket's run in the daemon, then follows it like `spool run next`. Any other ticket is refused: `T04 is ready, not awaiting approval`. `spool run reject <project> <ticket> --note "..."` sends it back to the implementer instead.

## Hold mode

```yaml
run:
  integration: hold     # default: local
```

With `hold`, an approved ticket is not merged: the merge policy's `hold_mode` rule holds it, with any other rule that holds, and it waits in `awaiting_approval` with its worktree kept:

```text
T04 needs you: hold_mode (run.integration is hold); approve with `spool run approve demo T04` or reject with `spool run reject demo T04 --note "..."` — worktree kept at /home/u/.spoolhq/worktrees/demo/T04
```

`spool run all` stops there. It is for users who want to look at each change before it lands on `main`.
