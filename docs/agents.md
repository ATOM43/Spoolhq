# Agents

A coding agent implements one ticket in its own worktree. SpoolHQ talks to agents through one interface, `AgentRunner`, so the run loop ([run-loop.md](run-loop.md)) does not care which backend is behind it. The first backend, `claude-code-cli`, drives the user's own installed `claude` CLI, so a Claude subscription is enough; there is no API key to manage.

This is the security core of SpoolHQ: the agent must not be able to touch anything outside its worktree. SpoolHQ does not enforce that itself. Claude Code does, in four layers that SpoolHQ configures and then checks took effect.

The code is `services/agents/`: the policy, budget, events and result in `model.py`, the interface in `runner.py`, the stream parser in `claude_stream.py`, the Claude Code adapter in `claude_cli.py`, with its command line, settings and environment in `claude_config.py`, the fake runner in `fake.py` and the backend registry in `backends.py`. It imports no other service package (an import-linter contract checks this); callers pass plain values in.

## The interface

```python
class AgentRunner(Protocol):
    name: str
    def detect(self) -> BackendInfo: ...
    def run(prompt, policy, budget, *, model=None, on_event, on_raw=None,
            cancel: threading.Event) -> RunResult: ...
```

- `detect()` says whether the backend is installed (and its version), logged in (auth method and billing: `subscription`, `api` or `unknown`) and able to enforce the policy, or why not (`reason`).
- `run()` calls `detect()` first and raises `BackendUnavailableError(reason)` when the backend isn't installed, isn't logged in or can't enforce the policy. `PolicyError` means the policy itself is unacceptable (a bad stack command, a worktree that overlaps the home folder). Everything that happens once the agent started is reported in the result's `outcome`; `run()` does not raise for it.
- `on_event(event)` gets the normalised events in order; `on_raw(dict)` gets every raw stream message, so T13 can write `transcript.jsonl` through the run log. Both run on the calling thread, never concurrently.
- `AgentPolicy.for_worktree(worktree, commands, home)` builds the policy from the absolute worktree path, `project.yaml`'s `commands` and the SpoolHQ home folder. `Budget(max_turns, max_usd, max_tokens, timeout_s=1800)` limits the run.

### Events

All are frozen dataclasses with a `kind`:

| Event | Fields | When |
| --- | --- | --- |
| `Started` | `model`, `tools`, `backend_version` | Claude Code's `init` passed the checks below. |
| `Message` | `text` | The agent wrote text. |
| `ToolCall` | `id`, `name`, `input_summary` | The agent called a tool; the input as JSON, cut to 2,000 characters. |
| `FileEdit` | `path` | An `Edit`, `Write`, `MultiEdit` or `NotebookEdit` inside the worktree succeeded; relative, `/`-separated. |
| `Usage` | `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_creation_tokens` | Each new assistant message (counted once per message id). |
| `PermissionDenied` | `tool`, `input_summary`, `reason` | A tool call was refused. Also logged as a warning. |
| `RateLimit` | `status`, `reset_at` | A `rate_limit_event` (`allowed`, `allowed_warning`, `rejected`), or `retrying` for an API retry on a rate limit. |

### Outcomes and the result

`RunResult` has `outcome`, `summary` (the final text; a longer one keeps its last 4,000 characters after a `[… 6,000 characters cut …]` line, so the closing `<progress>` block survives), `files_changed` (sorted, deduplicated, relative), `input_tokens`, `output_tokens`, `cost_micro_usd`, `reset_at`, `denials`, `num_turns`, `backend`, `backend_version`, `model`, `error` and `debug` (counters such as `unknown_events`).

| Outcome | From |
| --- | --- |
| `completed` | `result` with subtype `success` and no error. |
| `max_turns` | subtype `error_max_turns`. |
| `budget_exhausted` | subtype `error_max_budget_usd`, or the runner's token count went over `max_tokens`. |
| `usage_limited` | a rejected `rate_limit_event`, an assistant message with `error: "rate_limit"` and no later success, or a result error matching `usage limit` (optionally `…|<epoch seconds>`). `reset_at` is the reset time, or `None`. |
| `timed_out` | `timeout_s` passed. |
| `cancelled` | the `cancel` event was set. |
| `error` | anything else; `error` holds the text and the last 50 lines of stderr. A policy check failing gives `policy not enforced: …`. |

## Roles and backends

`project.yaml` picks a backend per role: `agents.planner`, `agents.implementer` and `agents.reviewer`, each falling back to `agents.default` ([project.yaml](project-yaml.md)). `backends.py` holds the registry from backend name to adapter factory; today it knows only `claude-code-cli` (tests add fakes). An unknown name is refused when `project.yaml` loads, naming the field.

The daemon builds each role's runner per project for every run (`Agents.for_project`), and the planner's when a plan starts; `spool plan generate` and `spool review` use the project's `agents.planner` and `agents.reviewer`.

Each backend takes an optional `base_url` and `model` under `agents.backends`:

```yaml
agents:
  default: claude-code-cli
  backends:
    claude-code-cli: { base_url: http://localhost:11434, model: qwen3-coder }
```

- `base_url` must be http or https, plain http only for `localhost`, `127.0.0.1` and `::1`, with no username or password.
- For Claude Code, `base_url` becomes `ANTHROPIC_BASE_URL` in the `claude` process's environment and `model` becomes `--model` ([Claude Code environment variables](https://code.claude.com/docs/en/env-vars); `--model` overrides `ANTHROPIC_MODEL`). They are set for that child only; SpoolHQ never writes `~/.claude`, `~/.claude.json` or any other config of the user's. A daemon's own `ANTHROPIC_BASE_URL` is never passed on; without `base_url` and `model`, the command line and environment are as before.

### A custom endpoint never gets your login

Without its own credential, an agent CLI pointed at a custom `base_url` would send your subscription login there. So with a `base_url`, SpoolHQ supplies the credential itself:

- **An endpoint on this machine** (`localhost`, `127.0.0.1`, `::1`) gets the fixed dummy token `spoolhq-local-endpoint`; local servers such as Ollama ignore it.
- **A remote endpoint** gets `SPOOLHQ_ENDPOINT_TOKEN_<BACKEND>` from the daemon's environment (`SPOOLHQ_ENDPOINT_TOKEN_CLAUDE_CODE_CLI`, `SPOOLHQ_ENDPOINT_TOKEN_CODEX_CLI`), else the OS keychain, stored with `spool secrets set endpoint:<backend>` (hidden prompt; service `spoolhq`, key `endpoint:<backend>`). Without one the backend is refused before anything starts:

  ```text
  custom endpoint https://llm.example.com needs its own token; run spool secrets set endpoint:claude-code-cli
  ```

For Claude Code the token becomes `ANTHROPIC_AUTH_TOKEN`, which outranks the saved claude.ai login; Claude Code keeps that login on the machine but doesn't send it ([authentication precedence](https://code.claude.com/docs/en/authentication#authentication-precedence), [subscriptions and gateways](https://code.claude.com/docs/en/llm-gateway#subscriptions-and-gateways)). `ANTHROPIC_API_KEY` is never passed with a custom endpoint, and `claude auth status` isn't consulted: the login line of `detect()` reads `endpoint token` and billing is `unknown`. `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` keeps the token out of the agent's commands.

`spool agents --project <name>` prints the backend, model and endpoint of each role:

```text
planner      claude-code-cli  model: qwen3-coder  endpoint: http://localhost:11434
implementer  claude-code-cli  model: qwen3-coder  endpoint: http://localhost:11434
reviewer     claude-code-cli  model: qwen3-coder  endpoint: http://localhost:11434
```

### Local models with Ollama

Ollama serves an Anthropic-compatible API, so Claude Code can drive a local model:

1. Install Ollama and pull a coding model with tool use, e.g. `ollama pull qwen3-coder`.
2. Point the backend at it in `project.yaml`:

   ```yaml
   agents:
     backends:
       claude-code-cli: { base_url: http://localhost:11434, model: qwen3-coder }
   ```

3. Check with `spool agents --project <name>`.

SpoolHQ hasn't been tested against a real local model. Keep in mind:

- Claude Code gets SpoolHQ's dummy token, never your login ([above](#a-custom-endpoint-never-gets-your-login)). Plain http is still limited to this machine.
- The policy checks still apply: the model must work through Claude Code's tools, and the run stops if `init` lists the wrong tools.
- Local models are much weaker at multi-step tool use; set it per role (for example only `agents.reviewer`) if you want to try one.

## The four policy layers

| Layer | What it does | Enforced by |
| --- | --- | --- |
| 1. `--restricted` | Removes the command-running tools unless `--tools` names them, confines the built-in file tools to the worktree, loads only managed settings and `--settings` (a repository's `.claude/settings.json` and its hooks are never loaded), refuses `bypassPermissions`. | Claude Code |
| 2. An allowlist | `--permission-mode dontAsk` with `--permission-prompts none`: nothing that isn't pre-approved runs, and denials are reported as `permission_denied` messages and in the result's `permission_denials`. `--disallowedTools WebFetch WebSearch mcp__*` and `--strict-mcp-config` remove web and MCP tools. | Claude Code |
| 3. The OS sandbox | Bash commands run in bubblewrap (Linux) or Seatbelt (macOS): writes only to the worktree, a temp folder and the main repository's `.git` (not its `hooks/` or `config`), no network, and the credential files below denied. | The operating system, configured by Claude Code |
| 4. A scrubbed environment | The `claude` process gets only allowlisted variables; Claude Code removes its own credentials from the commands it runs. | SpoolHQ (`child_env`) and Claude Code |

SpoolHQ never passes `--dangerously-skip-permissions` or `bypassPermissions`; a test fails if either appears in `services/agents/` outside comments and docstrings.

**Checking it took effect.** The first message of every run is `system`/`init`. If it lists any tool that wasn't requested (anything outside `--tools`, any `mcp__*`, `WebFetch` or `WebSearch`) or a permission mode other than `dontAsk`, the parser raises `PolicyViolation` and the adapter stops the run with outcome `error` and `policy not enforced: …`. A message before `init` is a violation too. One exception: with `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`, Claude Code 2.1.302 forces and reports the `default` mode; with `--permission-prompts none` every call that would prompt there is denied as in `dontAsk`, so the adapter also accepts `default` (DECISIONS 98), but only when that variable is `1` in the environment actually passed to `claude` and `--permission-prompts none` is on its command line (`permission_modes(env, argv)`); otherwise `default` is a violation too. Every other mode stops the run.

### The command line

Built as a list (`build_argv`), in this order; the prompt goes on stdin, never in argv, so it isn't visible in the process list and has no length limit below Claude Code's 10 MB stdin cap:

```text
claude -p --output-format stream-json --verbose --restricted
  --permission-mode dontAsk --permission-prompts none
  --tools Read,Edit,Write,Glob,Grep,Bash
  --allowedTools Read Edit Write Glob Grep <Bash rules…>
  --disallowedTools WebFetch WebSearch mcp__*
  --strict-mcp-config --no-session-persistence
  --max-turns <n> [--max-budget-usd <x>, API billing only] [--model <m>]
  --settings <json>
```

`--settings`:

```json
{"sandbox": {"enabled": true, "failIfUnavailable": true, "allowUnsandboxedCommands": false,
             "autoAllowBashIfSandboxed": false,
             "network": {"allowedDomains": [], "strictAllowlist": true},
             "credentials": {"files": [{"path": "~/.ssh", "mode": "deny"}, …]}},
 "disableAllHooks": true}
```

`autoAllowBashIfSandboxed` defaults to `true` in Claude Code, which would approve every sandboxed command whether or not it is on the allowlist, so it is set to `false`.

## Read-only policies

The reviewer ([review](review.md)) and the planner ([planner](planner.md)) read code but must not change it or run anything; the planner's working folder is the project's repository. `AgentPolicy.read_only_for(worktree, home)` builds a policy with `read_only=True`, no stack commands and no git commands; the deny list is the same. For it the adapter passes `--tools Read,Glob,Grep` and `--allowedTools Read Glob Grep`, with no `Bash(…)` rules, no `Edit` and no `Write`, and `init` must list exactly those three tools: any other, or a missing one, is a policy violation (`policy not enforced: …`). `--restricted`, `dontAsk`, the sandbox settings and the scrubbed environment stay as for a writing policy, whose command line is unchanged.

## The allowlist

The implementer may run the project's stack commands from `project.yaml` except `install` (`lint`, `test` and any others it defines) and read-only git. Installs run only in the gates, outside the sandbox, where the network is available (`Commands.for_implementer()`); its prompt doesn't list `install` either. The read-only git commands are `git status`, `git diff`, `git log`, `git show`. Each becomes two permission rules: exact (`Bash(just test)`) and prefix (`Bash(just test *)`, which allows `just test -k foo`). The file tools `Read`, `Edit`, `Write`, `Glob` and `Grep` are allowed as a whole; layer 1 confines them to the worktree.

A stack command is refused with `PolicyError` if it contains any of `; & | < > $ ` ( ) * ? [ ] { } \`, a newline, or leading or trailing spaces, because it would widen the rules:

```text
commands.test: 'just test; rm -rf ~' contains shell operators or wildcards; use a plain command
commands.lint: ' just lint' has leading or trailing spaces; use a plain command
```

## The sandbox is required

Because the agent writes the tests that `just test` runs, the allowlist alone is not a boundary: an allowed command runs whatever code the agent put in the worktree. The OS sandbox is. So:

- **Native Windows is refused**: Claude Code's sandbox is not available there. `detect()` reports `policy enforceable: no` with a message pointing to WSL2; run SpoolHQ inside WSL2.
- **Linux needs bubblewrap and socat.** Without `bwrap` or `socat` on `PATH` the backend is refused with an install hint:
  - Fedora: `sudo dnf install bubblewrap socat`
  - Debian / Ubuntu: `sudo apt install bubblewrap socat`
- **macOS** uses Seatbelt, which is built in.
- `failIfUnavailable: true` backs this up inside Claude Code: if the sandbox can't start, Claude Code refuses to run instead of running unsandboxed.

Network: none for the agent's commands in v1 (`allowedDomains: []`, `strictAllowlist: true`). Installs are run by the gates as code, outside the agent.

The worktree must not be, or contain, the user's home folder or the SpoolHQ home, and must not overlap a denied path, since sandboxed commands may write anywhere in it.

## The environment allowlist

The `claude` process gets only these variables from the daemon's environment: `PATH`, `HOME`, `USER`, `LOGNAME`, `LANG`, `LC_*`, `TMPDIR`, `TMP`, `TEMP`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME`, `XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS`, `CLAUDE_CONFIG_DIR`, `HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY`, `https_proxy`, `http_proxy`, `no_proxy`, `NODE_EXTRA_CA_CERTS`, `SSL_CERT_FILE`, and on Windows `SYSTEMROOT`, `USERPROFILE`, `APPDATA`, `LOCALAPPDATA`, `COMSPEC`, `PATHEXT`. It always adds `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` and `DISABLE_AUTOUPDATER=1`, and `ANTHROPIC_BASE_URL` with `ANTHROPIC_AUTH_TOKEN` when the backend has a `base_url` ([roles](#roles-and-backends)).

`ANTHROPIC_API_KEY` is passed only for API billing. If it were in the environment, Claude Code would bill the API instead of the subscription, so a subscription login always wins: `detect()` checks `claude auth status` without the key first, and offers the key only when there is no subscription login. Tokens such as `GITHUB_TOKEN`, `CLICKUP_TOKEN` and `SPOOLHQ_TOKEN` never reach the agent.

`detect()` runs `claude --version` and `claude auth status` as argument lists, with a 15 s timeout and the same scrubbed environment. Claude Code 2.1.259 or newer is required (`--permission-prompts` first shipped there); an older one is refused with `Claude Code 2.1.200 is too old; SpoolHQ needs 2.1.259 or newer (run: claude update)`.

## The credential deny list

Sandboxed commands may not read: `~/.ssh`, `~/.aws`, `~/.config/gh`, `~/.gnupg`, `~/.netrc`, `~/.docker/config.json`, `~/.kube`, `~/.git-credentials`, `~/.config/git/credentials`, `~/.npmrc`, `~/.pypirc`, `~/.local/share/keyrings`, Claude Code's own `~/.claude` and `~/.claude.json` (and the `CLAUDE_CONFIG_DIR` folder when that variable is set in the environment passed to `claude`), and the SpoolHQ home folder, which holds the API token.

Worktrees live inside the SpoolHQ home by default (`~/.spoolhq/worktrees/<project>/<ticket>`), and denying the whole folder would deny the worktree too. Then the list holds the token file plus every entry of the home except the folders on the way down to the worktree (`config.toml`, `logs/`, other projects' worktrees, …).

## Running a process

- `subprocess.Popen(argv, cwd=worktree, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=…, encoding="utf-8", errors="replace")`, in its own process group on POSIX (`start_new_session=True`). Never `shell=True`.
- The prompt is written to stdin by a writer thread, which then closes it. A reader thread pushes stdout lines to a queue that the calling thread parses; another keeps the last 50 stderr lines for `RunResult.error`.
- **Limits**: `max_turns` and (API billing) `max_usd` are Claude Code's; `max_tokens` is counted by the runner from the parsed usage and stops the run with `budget_exhausted`; `timeout_s` gives `timed_out`; setting `cancel` gives `cancelled`.
- **Stopping**: SIGINT to the process group (Claude Code ends the turn), 10 s, then SIGTERM (it exits and kills running Bash children), 5 s, then SIGKILL. On Windows: `terminate()`, 5 s, then `kill()`.
- **Teardown always runs**: whatever happens, the process is stopped, anything left in its process group is killed, and the pipes are closed.
- **Scrub stubs are removed.** With `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`, Claude Code 2.1.302 creates empty placeholders in its working folder (`.env`, `.env.local` and the other `.env.*` files, `.gitmodules`, `.npmrc`, `.yarnrc`, `.yarnrc.yml`, `bunfig.toml`, `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `.claude/agents/`, `.claude/commands/`, `node_modules/.bin/`) and leaves them behind; existing files are not touched. After a run, the adapter removes each of these that wasn't in the worktree before and is still empty, so they never reach the diff. `detect()` runs `claude --version` and `claude auth status` in a throwaway temp folder, because `auth status` creates them too.

## Usage limits

A subscription usage limit is not a failure. The runner returns outcome `usage_limited` with `reset_at` (from the `rate_limit_event`'s `rate_limit_info.resetsAt`, or the epoch after `usage limit…|` in the error text, or `None` if neither is known), and `error` is `None`. The run loop turns it into a paused run that resumes after `reset_at` ([run-loop.md](run-loop.md#paused-blocked-cancelled-interrupted)).

The `rate_limit_event` fields, as observed from Claude Code 2.1.302 and in the Agent SDK's `SDKRateLimitEvent` type: `{"type": "rate_limit_event", "rate_limit_info": {"status": "allowed" | "allowed_warning" | "rejected", "resetsAt": <epoch seconds>, "rateLimitType": …, …}}`. Values above 10¹¹ are read as milliseconds.

## Cost and tokens

- **Tokens**: `input_tokens` counts every input token: uncached, cache writes and cache reads; `cache_read_tokens` the part of it read from the cache; `output_tokens` the output. They come from the `result` message's `usage`, or, without one, from the assistant messages, each message id counted once. `Usage` events keep the breakdown. The `max_tokens` budget compares weighted tokens: input plus output, with cache reads counting a tenth.
- **Cost**: subscription runs report `cost_micro_usd=None`, even though Claude Code prints an estimate. API-key runs report `total_cost_usd` converted to integer micro-USD with `Decimal` (`0.0123` → `12300`), like the run log stores it.

## The fake runner

`FakeRunner(transcript, *, name="fake", stall_s=0)` replays a recorded stream-json file through the same `ClaudeStreamParser` and calls the same callbacks (with the same tool check, read-only included), so tests can drive agent runs without a model or network. For a `Write` inside the worktree it writes the given content, so file effects can be tested. Given a list of transcripts, each `run()` replays the next one and a run past the end raises, so retries can be tested; `calls` holds each run's prompt and policy. Its `detect()` reports installed, logged in, `subscription`, enforceable. Transcripts live in `daemon/tests/fixtures/agents/claude/`; `recorded/real_run.jsonl` is an anonymised recording of the opt-in real run below.

The adapter itself is tested end to end with `daemon/tests/services/agents/fake_claude.py`, a stand-in `claude` binary that records its argv, environment and stdin and prints a scenario.

**The contract suite** (`tests/services/agents/test_contract.py`) is one parametrised file every adapter must pass: a run that creates a file, a denied command reported and logged, a usage-limit pause with its reset time, a timeout, a cancel, and usage reported and weighted (cache reads count a tenth toward `max_tokens`). It runs over a list of `AdapterCase`s: the Claude Code adapter through the fake binary and the recorded transcripts, and `FakeRunner` (whose `stall_s` makes it hang like a stuck agent, so timeout and cancel apply). A new adapter adds one entry.

**The real run** (`tests/services/agents/test_real_run.py`, marker `real_agent`) uses the installed `claude` and your subscription. It is skipped unless `SPOOLHQ_REAL_AGENT=1` and `claude auth status` says you are logged in:

```sh
SPOOLHQ_REAL_AGENT=1 uv run --directory daemon pytest -m real_agent
SPOOLHQ_REAL_AGENT=1 SPOOLHQ_RECORD=1 uv run --directory daemon pytest -m real_agent   # also re-record
```

## `spool agents`

Lists the detected backends, for now only `claude-code-cli` (with `--project <name>`, the roles instead; see [roles](#roles-and-backends)):

```text
claude-code-cli
  installed  yes (2.1.302)
  login      yes (claude.ai, subscription)
  policy     yes (enforceable)
```

It exits 0 even when nothing is installed; the output then says how to install Claude Code and log in (`claude auth login`).

## Known limits

- **Sandboxed commands can still read files not on the deny list.** The sandbox restricts writes and network, not reads in general; a test the agent writes can read other files in your home folder. It cannot send them anywhere (no network) or write them outside the worktree and the temp folder, but it could copy them into the worktree, where they would end up in the diff. Docker isolation (later phase) closes this.
- **`files_changed` comes from the file tools.** A file changed by a command (`just install` writing a lockfile, a code generator) is not in it; the run loop takes the files changed from git instead.
- **Scrub stubs at the top of the worktree.** During a run the placeholders above exist in the worktree (Claude Code probably uses them to write-protect those files for sandboxed commands; not verified). An agent that legitimately creates one of these as an empty file loses it at cleanup.
- **The temp folder is writable.** Sandboxed commands may write to the system temp folder, which other processes can read.
- Claude Code's `permission_denied` messages are best-effort; the result's `permission_denials` is the complete list, and the parser reports a denial found only there too.
