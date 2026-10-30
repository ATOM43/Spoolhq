# SpoolHQ

SpoolHQ is an open-source, local-first desktop app that turns a written spec into a ticket plan, then has a coding agent implement the tickets one at a time, with tests and review before each merge. A Python daemon runs the loop, a `spool` CLI drives it, and a Tauri desktop app shows what is happening.

**Status: pre-alpha, not usable yet.** The daemon serves a minimal authenticated API and the desktop app shows whether it is running. The CLI can create a project, read and edit its tickets, check the plan and change ticket statuses, and show the run log and worktrees. The daemon records runs and manages the git worktree each run works in, can drive Claude Code under a locked-down policy and can run a project's quality gates, but nothing starts agent runs yet.

## Development quickstart

Install [uv](https://docs.astral.sh/uv/), [Node.js 24 LTS](https://nodejs.org/), [pnpm](https://pnpm.io/) and [just](https://just.systems/), then:

```sh
just install && just test
```

## Create a project and look at its tickets

A project is a workspace folder in `~/spoolhq-projects/` for an existing git repository (`SPOOLHQ_PROJECTS_DIR` to use another folder):

```sh
uv run --directory daemon spool init my-app --repo ~/code/my-app   # creates ~/spoolhq-projects/my-app/
uv run --directory daemon spool project validate my-app
```

Or generate a new repository from a template that already passes its own gates, so the plan starts at the real work ([templates](docs/templates.md)):

```sh
uv run --directory daemon spool templates list
uv run --directory daemon spool init my-app --repo ~/code/my-app --template fastapi-react
uv run --directory daemon spool templates check fastapi-react   # generate in a temp folder, run install/lint/test
```

Write the spec in the workspace's `CONTEXT.md`, then let the planner draft the tickets, review them and approve ([planner](docs/planner.md)). Nothing runs until you approve:

```sh
uv run --directory daemon spool plan generate my-app [--template-description stack.md]   # default: the template's description
uv run --directory daemon spool plan show my-app            # drafts, estimates, dependencies, problems
uv run --directory daemon spool tickets edit my-app T03     # an edited draft survives a re-plan
uv run --directory daemon spool plan approve my-app         # every draft → ready, in one step
```

Tickets are markdown files in the workspace's `tickets/` folder; you can also write them by hand ([format](docs/ticket-format.md), [plan rules](docs/scheduler.md)):

```sh
uv run --directory daemon spool tickets list my-app [--status ready] [--phase 1]
uv run --directory daemon spool tickets show my-app T01
uv run --directory daemon spool tickets edit my-app T01     # opens $VISUAL / $EDITOR
uv run --directory daemon spool plan check my-app           # dependencies, cycles, duplicates
uv run --directory daemon spool plan next my-app            # the ticket that runs next
uv run --directory daemon spool plan summary my-app         # counts, hours left, critical path
uv run --directory daemon spool tickets set-status my-app T01 running
```

Each run of a ticket and its attempts are recorded in the workspace's `.spoolhq/state.db` ([run log](docs/runs.md)); nothing starts runs yet, but you can read them:

```sh
uv run --directory daemon spool runs list my-app [--ticket T04]   # newest first: status, attempts, tokens
uv run --directory daemon spool runs show my-app 12               # one run and its attempts' folders
```

Each run works in its own git worktree, `~/.spoolhq/worktrees/<project>/<ticket>`, on a `feat/<ticket>-<slug>` branch made from the default branch; the main working copy must be clean and is never changed ([git](docs/git.md), git 2.36 or newer). To see them:

```sh
uv run --directory daemon spool worktrees list my-app      # ticket, branch, path, state (ok, missing folder, ...)
```

Agents run through your own installed [Claude Code](https://code.claude.com/docs/en/setup) CLI (2.1.259 or newer, logged in with `claude auth login`), confined to the ticket's worktree by Claude Code's restricted mode, an allowlist of the project's commands, the OS sandbox with no network and a scrubbed environment ([agents](docs/agents.md)). Native Windows is not supported (use WSL2); on Linux the sandbox needs `bubblewrap` and `socat` (`sudo dnf install bubblewrap socat` on Fedora). To check:

```sh
uv run --directory daemon spool agents      # installed, version, login and billing, policy enforceable
```

To see the prompt an agent would start a ticket with ([context](docs/context.md)); its size and anything trimmed to fit `context.max_chars` (`project.yaml`, default 120,000 characters) go to stderr:

```sh
uv run --directory daemon spool prompt show my-app T04
```

To run a project's quality gates (`install`, then `lint` and `test`) in a folder, without a shell and in a scrubbed environment ([gates](docs/gates.md)); it prints one line per gate, each failing gate's excerpt and the failing tests, and exits 1 unless all pass:

```sh
uv run --directory daemon spool gates run my-app [--path <dir>]   # default: the project's repository
```

To have a second, read-only agent review a ticket's committed work against its "Done when" items ([review](docs/review.md)); it prints ✓/✗ per item, the verdict and a summary, and exits 0 for `approve`, 1 for `changes_requested` or `needs_human`, 2 if the run didn't finish:

```sh
uv run --directory daemon spool review my-app T07 [--path <worktree>] [--base <ref>]   # diff: <base>...HEAD
```

## Run tickets

With the daemon running (below), the run loop takes a ready ticket through its worktree, the implementer, the gates and the reviewer, with retries ([run loop](docs/run-loop.md)). An approved ticket becomes one commit on the local default branch, tagged `ticket/<id>`, with its `PROGRESS.md` entry ([integration](docs/integration.md)); with `run.integration: hold` it waits for `spool run approve`. With `git.remote` set, it is pushed to GitHub first; the daemon polls pull requests ([GitHub delivery](docs/github.md)). The [merge policy](docs/merge-policy.md) sends a ticket to a person instead when it is `review_required`, its diff is over 400 lines, it touches a protected path (CI, migrations, auth, dependencies, agent instructions) or the reviewer said `needs_human`: a pull request with `git.remote`, else `spool run approve` or `spool run reject --note`.

```sh
uv run --directory daemon spool run next my-app [T04]   # start and follow: one line per phase change
uv run --directory daemon spool run all my-app          # ready tickets one after another
uv run --directory daemon spool run status my-app
uv run --directory daemon spool run pause|resume|cancel my-app [--run 12]
uv run --directory daemon spool run approve my-app T04    # merge a ticket waiting in awaiting_approval (alias: integrate)
uv run --directory daemon spool run reject my-app T04 --note "rename the endpoint"  # send it back
uv run --directory daemon spool run discard my-app T04  # remove an interrupted or blocked ticket's worktree
uv run --directory daemon spool secrets set github      # the GitHub token for pull requests (hidden prompt)
uv run --directory daemon spool github sync my-app      # check the project's open pull requests now
```

Ctrl-C stops following, not the run: it continues in the daemon.

## Run the daemon

```sh
uv run --directory daemon spool serve     # or: just dev
```

The daemon listens on `http://127.0.0.1:8765` only; the interactive API docs are at `/docs`. On first start it writes a random access token to `~/.spoolhq/token` (readable only by you); the `spool` CLI reads it from there, and every `/api/*` route except `/api/health` needs it as `Authorization: Bearer <token>`. Settings live in `~/.spoolhq/config.toml` (`port`, `log_level`) and can be overridden with `SPOOLHQ_PORT` and `SPOOLHQ_LOG_LEVEL` (`spool serve` has no `--port` flag); set `SPOOLHQ_HOME` to use another folder. Logs are JSON lines in `~/.spoolhq/logs/daemon.log`. Only one daemon runs at a time: a second `spool serve` exits with `another SpoolHQ daemon is already running (pid …)`. On start, the daemon marks runs that a stopped daemon left active as `interrupted` and removes the worktrees they left behind, except those of blocked runs, runs awaiting approval and the runs it just marked interrupted.

`uv run --directory daemon spool version` prints the CLI's version and, if the daemon is running, the daemon's.

## Run the desktop app

The desktop app is a [Tauri 2](https://tauri.app/) window around a React UI. It finds the daemon through `~/.spoolhq/` (or `SPOOLHQ_HOME`) and shows whether it is reachable; it does not start the daemon itself.

### Prerequisites

Everything from the development quickstart, plus [Rust via rustup](https://rustup.rs/) (the toolchain version is pinned in `rust-toolchain.toml` and installed on first use) and your platform's packages:

- **Fedora**

  ```sh
  sudo dnf install webkit2gtk4.1-devel openssl-devel curl wget file \
    libappindicator-gtk3-devel librsvg2-devel libxdo-devel
  sudo dnf group install c-development
  ```

- **Ubuntu / Debian**

  ```sh
  sudo apt update
  sudo apt install libwebkit2gtk-4.1-dev build-essential curl wget file \
    libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev
  ```

- **macOS**: the Xcode Command Line Tools (`xcode-select --install`).
- **Windows**: [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) with "Desktop development with C++", and the WebView2 runtime (already installed on Windows 10 1803+ and Windows 11).

### Start it

```sh
just install
just dev        # starts the daemon and the app together; Ctrl-C stops both
```

`just daemon` and `just desktop` start either one alone. The top bar shows **Daemon ok · v…** when the daemon answers, **Reconnecting…** while it retries after losing it (every 3 s), and **Daemon not running** when nothing answers; in that case Home shows the `spool serve` command and a **Retry** button.

The access token never reaches the web view: the Rust side reads `~/.spoolhq/token` and adds it to each daemon request.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow and [DECISIONS.md](DECISIONS.md) for why things are the way they are.

## Licence

[Apache-2.0](LICENSE)
