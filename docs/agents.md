# Agents

A coding agent implements one ticket in its own worktree. SpoolHQ talks to agents through one interface, `AgentRunner`, so the run loop ([run-loop.md](run-loop.md)) does not care which backend is behind it. The first backend, `claude-code-cli`, drives the user's own installed `claude` CLI, so a Claude subscription is enough; there is no API key to manage. The second, `codex-cli`, drives the user's own `codex` the same way ([Codex CLI](#codex-cli-codex-cli)). The third, `claude-agent-sdk`, is for users with an Anthropic API key instead of a subscription ([Claude Agent SDK](#claude-agent-sdk-claude-agent-sdk)).

This is the security core of SpoolHQ: the agent must not be able to touch anything outside its worktree. SpoolHQ does not enforce that itself. Claude Code does, in four layers that SpoolHQ configures and then checks took effect; for Codex, its OS sandbox does, under a permission profile SpoolHQ writes for each run, and SpoolHQ refuses any part of the policy Codex can't enforce.

The code is `services/agents/`: the policy, budget, events and result in `model.py`, the interface in `runner.py`, the stream parser in `claude_stream.py`, the Claude Code adapter in `claude_cli.py`, with its command line, settings and environment in `claude_config.py`, the process handling both CLI adapters share in `process.py`, the Codex CLI adapter in `codex_cli.py`, `codex_config.py` and `codex_stream.py`, the Agent SDK adapter in `agent_sdk.py` (key, policy hook, runner) and `agent_sdk_stream.py` (its transport and run loop), the custom-endpoint token in `endpoint.py`, the fake runner in `fake.py` and the backend registry in `backends.py`. It imports no other service package (an import-linter contract checks this); callers pass plain values in.

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

`project.yaml` picks a backend per role: `agents.planner`, `agents.implementer` and `agents.reviewer`, each falling back to `agents.default` ([project.yaml](project-yaml.md)). `backends.py` holds the registry from backend name to adapter factory; it knows `claude-code-cli`, `codex-cli` and `claude-agent-sdk` (tests add fakes). An unknown name is refused when `project.yaml` loads, naming the field.

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

## Codex CLI (`codex-cli`)

`CodexCliRunner` drives the user's own `codex` (Codex CLI 0.166.0 or newer) with its ChatGPT or API-key login (`codex login`), or a [custom endpoint](#a-custom-endpoint-never-gets-your-login). It returns the same events and `RunResult` as the Claude Code adapter. Everything below was checked against the Codex docs at https://learn.chatgpt.com/docs on 2026-10-30, for Codex CLI 0.166.0 (the [command reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli), [non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode), [permissions](https://learn.chatgpt.com/docs/permissions), [sandbox](https://learn.chatgpt.com/docs/sandboxing), [approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security), the [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) and [environment variables](https://learn.chatgpt.com/docs/config-file/environment-variables)). Codex isn't installed on the machine this was written on, so the adapter is tested against a stand-in binary and hand-built transcripts only.

### The command line

Built as a list (`codex_config.build_argv`); the prompt goes to stdin (`-`), never in argv, and the worktree is the working folder and `--cd`:

```text
codex exec --json --ephemeral --ignore-user-config --ignore-rules --cd <worktree> [--model <m>]
  -c approval_policy="never"
  -c default_permissions="spoolhq"
  -c permissions.spoolhq=<the profile below>
  -c web_search="disabled"
  -c features.apps=false  -c features.plugins=false  -c features.hooks=false
  -c features.multi_agent=false  -c features.memories=false  -c tools.view_image=false
  -c allow_login_shell=false
  -c shell_environment_policy.ignore_default_excludes=false
  -c history.persistence="none"  -c check_for_update_on_startup=false
  [-c model_provider="spoolhq"
   -c model_providers.spoolhq={name="SpoolHQ endpoint",base_url="<url>",env_key="SPOOLHQ_ENDPOINT_TOKEN_CODEX_CLI"}]
  -
```

- **Never a bypass.** No `--dangerously-bypass-approvals-and-sandbox` (`--yolo`), `danger-full-access`, `--full-auto`, `--approve-for-me` or `--skip-git-repo-check`; a test fails if any appears in `services/agents/` outside comments and docstrings. `--sandbox` isn't passed either: it would switch Codex back to its older sandbox settings, which can't deny reads.
- **Unknown settings stop the run.** `--strict-config` makes Codex refuse any `-c` override it doesn't recognise ("unknown configuration field … in -c/--config override") before it starts, so a renamed key can't silently drop part of the policy. Real Codex 0.166.0 ignored `tools.view_image` without it.
- **Features off.** Besides web search, apps, plugins, hooks, multi-agent and memories, these 0.166.0 features are on by default and are turned off (`features.<name>=false`): `view_image`, `browser_use`, `browser_use_external`, `browser_use_full_cdp_access`, `computer_use`, `in_app_browser`, `remote_plugin`, `skill_mcp_dependency_install`, `tool_suggest`. `code_mode_host` stays on: without it the model's tool calls fail closed ("code-mode host is disabled").
- **Per-run settings, never the user's.** `--ignore-user-config` skips `$CODEX_HOME/config.toml` while "authentication still uses `CODEX_HOME`", so the login keeps working without a per-run `CODEX_HOME`. Project `.codex/` layers (config, hooks, rules) load only for trusted projects and trust is recorded in the user config, so a repository's `.codex/` is skipped; `--ignore-rules` skips execpolicy `.rules` and `features.hooks=false` turns hooks off. SpoolHQ writes nothing under `~/.codex`.

### The permission profile

A writing policy (the implementer) gets Codex's `:workspace` profile plus SpoolHQ's deny list; a read-only one (the reviewer and the planner) may read only the worktree and Codex's `:minimal` runtime paths and write nothing:

```toml
# implementer
{extends=":workspace", filesystem={"~/.ssh"="deny", …, "~/.codex"="deny"}, network={enabled=false}}
# reviewer, planner
{filesystem={":root"="deny", ":minimal"="read", ":workspace_roots"={"."="read"}, "~/.ssh"="deny", …}, network={enabled=false}}
```

The deny list is the [credential deny list](#the-credential-deny-list) plus Codex's own `~/.codex` and the `CODEX_HOME` folder when set; a worktree overlapping any of it is refused, as for Claude Code.

Codex runs its own binary again inside bubblewrap, and the standalone installer puts it in `~/.codex/packages/standalone/releases/<version>/`. When the `codex` on `PATH` resolves into a denied Codex folder, that folder isn't denied as a whole: every entry is, except the folders on the way down to the release (the same rule as for a worktree inside the SpoolHQ home; symlinks are skipped, since bubblewrap can't mount over them and their targets are denied on their own). So `auth.json`, sessions and logs stay unreadable while the release (binaries only) can run. A read-only profile also gets `"<release>"="read"`, since `:root` is denied there and `:minimal` doesn't cover it.

### The policy mapping

| Part | Roles | How Codex enforces it |
| --- | --- | --- |
| Writes confined to the worktree | implementer | The `:workspace` profile: commands and file edits write only in the workspace root (the worktree) and the temp folders (all of `/tmp` on Linux: a real run wrote to a folder under `/tmp` outside its worktree, so a worktree in a temp folder is [refused](#refusals)); its `.git`, `.agents` and `.codex` stay read-only. Bubblewrap and seccomp on Linux, Seatbelt on macOS; Codex refuses a command it can't sandbox. |
| Read-only | reviewer, planner | A profile with no `write` entry, reads confined to the worktree and `:minimal`. A file change by a read-only run stops it (`policy not enforced: …`). |
| Approvals never asked | all | `approval_policy="never"`: nothing waits for a person and no command is escalated outside the sandbox. |
| Network off | all | `network={enabled=false}` for the agent's commands, `web_search="disabled"`, apps (connectors), plugins and multi-agent off; MCP servers come only from the config files SpoolHQ doesn't load, and an `mcp_tool_call` or `web_search` item stops the run. |
| Denied reads | all | Every denied path is `deny` (no reads, no writes) in the profile, enforced by the same OS sandbox. |
| The shell allowlist | all | Codex has no per-command allowlist. The OS sandbox with network off and denied reads stands in for it (below). |

**Why the sandbox stands in for the allowlist.** For Claude Code the allowlist isn't the boundary either: the implementer may run `just test`, which runs whatever tests the agent wrote, so the OS sandbox is what keeps it in ([the sandbox is required](#the-sandbox-is-required)). Codex's sandbox gives the same boundary: writes only to the worktree and temp folders, no network, the credential files unreadable; installs, lint and tests still run in the gates, outside the agent, before anything merges. The difference: a Codex implementer can run any command in that sandbox, not only the stack commands, and a Codex reviewer or planner can run read-only commands where Claude Code's has no shell at all. Neither can write outside the worktree, reach the network or read the denied files.

**A warning for a Codex reviewer or planner.** Because of that difference, `spool agents` prints a `warning` line under `codex-cli`, `spool agents --project <name>` prints one on stderr for each read-only role set to `codex-cli`, and each run logs it as a warning when it starts:

```text
warning: the reviewer uses codex-cli, which can run read-only shell commands (Claude Code's has no shell)
```

It is a warning only; nothing is refused for it.

### Refusals

`run()` checks the parts for the policy's role before starting anything, and `spool agents` shows them. A part Codex can't enforce here is refused with BackendUnavailableError, never weakened:

```text
backend 'codex-cli' can't enforce denied reads; choose another backend for the implementer role
```

| When | Parts not enforced |
| --- | --- |
| Linux without `bwrap` on `PATH` (Codex would fall back to a bundled helper that needs unprivileged user namespaces) | writes, read-only, network off, denied reads, the shell allowlist |
| `/etc/codex/config.toml` sets `sandbox_mode` or `[sandbox_workspace_write]` (Codex then ignores permission profiles), or can't be read | the same |
| Native Windows: the deny rules depend on a Windows sandbox setup SpoolHQ can't check; run inside WSL2 | denied reads, the shell allowlist |
| Any other OS | the sandbox parts |
| The worktree (symlinks resolved) is inside `/tmp`, `/var/tmp`, `$TMPDIR` or Python's `tempfile.gettempdir()`, where the sandbox lets the agent write anywhere | the whole run: `backend 'codex-cli' can't run in a worktree under /tmp: its sandbox can write anywhere there; set worktrees_dir outside temp folders`; `spool agents` checks `worktrees_dir` the same way (`worktrees  ok (…)` or `worktrees  no: …`) |
| Codex older than 0.166.0 | refused as too old: `Codex CLI 0.150.2 is too old; SpoolHQ needs 0.166.0 or newer (run: codex update)` |

### Events

| Codex `--json` | SpoolHQ |
| --- | --- |
| `thread.started` | `Started` (the configured model or `""`; Codex reports neither model nor tools) |
| `command_execution` item | `ToolCall` named `command_execution`, input the command |
| a failed command whose output says `Operation not permitted`, `Permission denied`, `Read-only file system`, `sandbox`, `Could not resolve host`, `Temporary failure in name resolution` or `Network is unreachable` | `PermissionDenied` (best effort: Codex reports no denial as such), also logged |
| completed `file_change` item | `ToolCall` named `file_change`, then a `FileEdit` per path inside the worktree |
| `agent_message` item | `Message`; the last one is the summary |
| `turn.completed` | `Usage` from `usage`: `input_tokens` (which includes the cached part), `output_tokens`, `cached_input_tokens`, `cache_write_input_tokens` |
| `turn.failed`, `error` | outcome `error` with the message, or `usage_limited` when it says `usage limit` |
| `reasoning`, `todo_list`, `error` items, `item.updated` | ignored (0.166.0 sends `error` items for config warnings) |
| anything else | counted in `debug.unknown_events` |

**What real Codex 0.166.0 leaves out of `--json`** (checked 2026-10-31): a command the sandbox stops from reading or writing files (`cat ~/.ssh/known_hosts`: `Permission denied`; a write to the home folder: `Read-only file system`) is not reported as an item at all, so SpoolHQ can't log those denials; the sandbox still blocks them. A blocked network call is reported (`curl: (6) Could not resolve host`) and logged. Calls the model makes through code mode can be missing too, so `files_changed` and `FileEdit` are best effort for Codex; the run loop takes the changed files from git, not from them. `file_change` paths are absolute and the model is never named. `daemon/tests/fixtures/agents/codex/recorded/real_sandbox_probe.jsonl` is a redacted real stream.

### Usage, limits and cost

- **Weighted tokens**: cached input counts a tenth, as for Claude Code. OpenAI's Codex credit table puts cached input at a tenth of input for GPT-6 Sol and GPT-6 Astra and a twentieth for GPT-6.1 Sol and Terra ([pricing](https://learn.chatgpt.com/docs/pricing)); SpoolHQ uses a tenth for every model, the more conservative of the two.
- **Usage limits**: Codex documents no reset time, so a usage-limit error gives `usage_limited` with `reset_at` `None` and the run loop pauses without one.
- **Budget**: `max_tokens` is checked against each turn's usage, which Codex reports only when the turn ends, and `codex exec` is one turn: the run finishes before it can go over, then ends `budget_exhausted` and the run loop blocks the ticket (`budget used up: 18,323 of 1,000 weighted tokens` in a real run), so `budget_per_ticket.tokens` stops further attempts but not the first one. `max_turns` and `max_usd` have no Codex option and aren't enforced; `timeout_s` and `cancel` work as for Claude Code (same process handling, `process.py`; a real 8 s timeout ended a `sleep 60` run `timed_out` after 8.5 s with nothing left running).
- **Cost**: `cost_micro_usd` is always `None`; Codex reports none.

### Environment, detection and endpoints

- The `codex` process gets the [environment allowlist](#the-environment-allowlist) plus the variables Codex documents: `CODEX_HOME` (where its login lives) and `CODEX_CA_CERTIFICATE`, and `npm_config_verify_deps_before_run=false`. `OPENAI_API_KEY` and `CODEX_API_KEY` are never passed; log in with `codex login --with-api-key` instead. `shell_environment_policy.ignore_default_excludes=false` removes variables named like `KEY`, `SECRET` or `TOKEN` from the agent's commands.
- `detect()` runs `codex --version` and `codex login status` (exit 0 when logged in; `ChatGPT` means `subscription`, `API key` means `api`) as argument lists in a temp folder, with a 15 s timeout and the same environment.
- A custom `base_url` becomes the per-run model provider `spoolhq` with `env_key="SPOOLHQ_ENDPOINT_TOKEN_CODEX_CLI"`; `requires_openai_auth` stays false, so the ChatGPT login isn't sent there, and the token follows the [custom-endpoint rule](#a-custom-endpoint-never-gets-your-login). Codex speaks only the Responses API (`wire_api = "responses"`); for Ollama use `base_url: http://localhost:11434/v1`. `model` becomes `--model`.

### Codex: known limits

- **Not every sandbox denial is reported.** Codex 0.166.0 leaves commands the sandbox stopped on the file system (a write outside the worktree, a `~/.ssh` read) out of `--json` entirely, so SpoolHQ can only log the denials that show up in the output, such as a blocked network call. The sandbox still blocks the rest; they just aren't in the run log.
- **The token budget can't stop a turn.** Codex reports usage only when its turn ends, and `codex exec` runs one turn, so `budget_per_ticket.tokens` stops further attempts (the ticket is blocked) but not the current one. The timeout (`timeout_s`) and cancel are what stop a run mid-way.
- **Only the standalone install was checked.** The real check used Codex from the standalone installer (`~/.codex/packages/…`). A Codex installed with npm runs a native binary from another package folder; whether a read-only profile can start it is unchecked.

## Claude Agent SDK (`claude-agent-sdk`)

`AgentSdkRunner` runs the [Claude Agent SDK for Python](https://code.claude.com/docs/en/agent-sdk/python) with an Anthropic API key, for users without a Claude subscription. It returns the same events and `RunResult` and passes the contract suite. Checked on 2026-10-31 against `claude-agent-sdk` **0.2.176** (MIT, pinned in `daemon/pyproject.toml`), which bundles Claude Code **2.1.316**, and the docs at https://code.claude.com/docs/en/agent-sdk/python, https://code.claude.com/docs/en/agent-sdk/overview, https://code.claude.com/docs/en/headless and https://code.claude.com/docs/en/authentication.

**It needs the Claude Code binary, and brings its own.** The SDK is a library that runs the Claude Code CLI; the wheel ships it in `claude_agent_sdk/_bundled/`. SpoolHQ uses that one (or `claude` on `PATH` if it is missing), and `spool agents` shows both versions.

**The same process as the Claude Code adapter.** The SDK's own transport starts the CLI with the daemon's whole environment (`ClaudeAgentOptions.env` is merged on top of it), so SpoolHQ hands `query()` its own `Transport` (a public SDK interface) that starts the CLI with the [Claude Code command line](#the-command-line) and the [scrubbed environment](#the-environment-allowlist), plus `--setting-sources=` (the SDK's `setting_sources=[]`) and `--input-format stream-json`. The four policy layers are therefore the same, and so is the `init` check. The SDK still runs its control protocol over that transport: the prompt goes to the CLI's stdin as a stream-json message (never argv), and the `PreToolUse` hook below is called for every tool use. Every stdout message is tapped before the SDK parses it, so `ClaudeStreamParser` sees exactly what it sees for the CLI adapter, and `on_raw` gets it for the transcript.

### The API key, and never a subscription login

- The key comes from `ANTHROPIC_API_KEY` in the daemon's environment, else the OS keychain (`spool secrets set anthropic`: hidden prompt, service `spoolhq`, key `anthropic`). It is never read from a file or argv and is put only into the environment of that run's CLI process; `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` keeps it from the agent's commands.
- Without one, nothing starts:

  ```text
  backend 'claude-agent-sdk' needs an API key; run spool secrets set anthropic
  ```

- **A stored claude.ai login is never used.** Each run gets a fresh, empty `CLAUDE_CONFIG_DIR` (removed afterwards, and denied to the agent's commands). Claude Code keeps its login under that folder (`.credentials.json` on Linux and Windows, and the macOS Keychain entry is keyed to it), so there is no login to find; it also means none of the user's settings, hooks, MCP servers or memory load and nothing is written to `~/.claude`. The key outranks any login anyway ("In non-interactive mode (`-p`), the key is always used when present"), and `init` must report `apiKeySource: "ANTHROPIC_API_KEY"`, or the run stops with `policy not enforced: init reports key source …`. Checked on this machine with Claude Code 2.1.316 and a stored claude.ai login: with the empty config folder and no key it answers `Not logged in · Please run /login`.
- `--bare` would also skip the login, but real 2.1.316 under `--bare` offered only Bash, Edit and Read (no Write, Glob or Grep) and never called the SDK's hook, so it is not used.
- A custom `base_url` gets the [endpoint token](#a-custom-endpoint-never-gets-your-login) as `ANTHROPIC_AUTH_TOKEN` (the dummy for localhost, `SPOOLHQ_ENDPOINT_TOKEN_CLAUDE_AGENT_SDK` or `spool secrets set endpoint:claude-agent-sdk` otherwise), never the API key; billing is then `unknown`. `model` becomes `--model`.

### The policy per role

Every part is enforced by Claude Code's own options (as for `claude-code-cli`) and again by the hook. All of them need the OS sandbox, so the backend is refused where Claude Code's sandbox can't run (native Windows, Linux without `bwrap` and `socat`), with T30's message: `backend 'claude-agent-sdk' can't enforce …; choose another backend for the <role> role`.

| Role | Tools (`--tools`, exact in `init`) | Writes | Bash |
| --- | --- | --- | --- |
| implementer | Read, Edit, Write, Glob, Grep, Bash | inside the worktree only | the stack commands except `install`, and `git status/diff/log/show`, with arguments |
| reviewer, planner | Read, Glob, Grep | none | none |

**The hook** (`check_tool`, registered for every tool with `HookMatcher(matcher=None)`) returns `permissionDecision: "deny"` with a reason, or nothing, in which case Claude Code's own rules still decide (it never returns `allow`). It denies:

- any tool outside the role's list (web fetch and search, MCP tools, subagents);
- a file tool whose path (absolute, `~/…` or relative to the worktree, symlinks resolved) is under a denied path (`~/.ssh`, the credential folders, `~/.claude*`, the SpoolHQ home: reads too) or outside the worktree; a `Glob` pattern that is absolute or has `..`;
- a Bash command with any of `; & | < > $ ` ( ) * ? [ ] { } \` or a newline (so `just test; curl x` is denied), one that `shlex` can't split, or whose argument list doesn't start with an allowed command's (`just test -k x` passes, `just tests` doesn't); `git … --output…`; and any call asking for `dangerouslyDisableSandbox`.

If the check itself raises, the call is denied. Each denial goes through the parser: a `PermissionDenied` event with the hook's reason, a warning in the log, and an entry in `denials` (Claude Code then also lists it in the result's `permission_denials`, counted once). Checked against real 2.1.316 with a local stand-in API that scripted the model's calls: `just test; curl x`, `cat ~/.ssh/known_hosts` and a `Read` of `/etc/hostname` were denied by the hook, the `Write` of `hello.txt` and `just test` ran, and a reviewer's `init` listed exactly Glob, Grep and Read. That stream is `daemon/tests/fixtures/agents/claude/recorded/agent_sdk_run.jsonl`.

### Usage, budget and errors

- Tokens and `total_cost_usd` come from the same stream as for Claude Code; billing is `api`, so `cost_micro_usd` is recorded.
- `budget_per_ticket.usd` becomes `--max-budget-usd`: Claude Code stops the run (`error_max_budget_usd` → `budget_exhausted`) once its cost estimate passes it, checked after each turn (a real 2.1.316 run stopped after its first turn). The estimate can overshoot by up to one turn. `max_turns` is `--max-turns`; `max_tokens`, the timeout and cancel are enforced by the runner as for the other adapters.
- Rate-limit and overload errors are retried by Claude Code itself (`api_retry` events, reported as `RateLimit(status="retrying")`), as the SDK documents. A billing or quota error (`billing_error`, "credit balance", "usage limits", "quota") is outcome `error`, never a pause, since an API key has no reset time: `the Anthropic API refused the key for billing or quota (…); add credit or raise the limit at https://platform.claude.com, then retry the ticket`.

### Agent SDK: testing and known limits

- Tests drive the real SDK client against `daemon/tests/services/agents/fake_sdk_cli.py`, a stand-in CLI that speaks the SDK's control protocol: it answers `initialize`, asks the hook before each recorded tool call (turning a denial into the error Claude Code returns), writes allowed `Write`s, and records argv, environment names, the key's SHA-256 and the prompt. The contract suite and a run-loop ticket (`tests/services/runloop/test_model.py`) run through it.
- The opt-in real run uses your API key and costs a few cents: `SPOOLHQ_REAL_BACKENDS=agent-sdk uv run --directory daemon pytest -m real_agent`. It is skipped, saying why, without the variable or a key. It has not been run yet (no key on the machine this was written on).
- The custom transport relies on the SDK's `Transport` class, which the SDK says may change in any release; the version is pinned.

## The fake runner

`FakeRunner(transcript, *, name="fake", stall_s=0)` replays a recorded stream-json file through the same `ClaudeStreamParser` and calls the same callbacks (with the same tool check, read-only included), so tests can drive agent runs without a model or network. For a `Write` inside the worktree it writes the given content, so file effects can be tested. Given a list of transcripts, each `run()` replays the next one and a run past the end raises, so retries can be tested; `calls` holds each run's prompt and policy. Its `detect()` reports installed, logged in, `subscription`, enforceable. Transcripts live in `daemon/tests/fixtures/agents/claude/`; `recorded/real_run.jsonl` is an anonymised recording of the opt-in real run below.

The adapter itself is tested end to end with `daemon/tests/services/agents/fake_claude.py`, a stand-in `claude` binary that records its argv, environment and stdin and prints a scenario.

**The contract suite** (`tests/services/agents/test_contract.py`) is one parametrised file every adapter must pass: a run that creates a file, a denied command reported and logged, a usage-limit pause with its reset time, a timeout, a cancel, and usage reported and weighted (cache reads count a tenth toward `max_tokens`). It runs over a list of `AdapterCase`s: the Claude Code adapter through the fake binary and the recorded transcripts, the Codex CLI adapter through the same binary as `codex` and the transcripts in `daemon/tests/fixtures/agents/codex/` (hand-built from the documented event format and checked against real 0.166.0 output, which `recorded/` holds; its denial is reported as `command_execution` and its usage limit has no reset time), and `FakeRunner` (whose `stall_s` makes it hang like a stuck agent, so timeout and cancel apply). A new adapter adds one entry. `tests/services/runloop/test_model.py` also runs a ticket end to end through the run loop with Codex as implementer and reviewer.

**The real run** (`tests/services/agents/test_real_run.py`, marker `real_agent`) uses the installed `claude` and your subscription. It is skipped unless `SPOOLHQ_REAL_AGENT=1` and `claude auth status` says you are logged in:

```sh
SPOOLHQ_REAL_AGENT=1 uv run --directory daemon pytest -m real_agent
SPOOLHQ_REAL_AGENT=1 SPOOLHQ_RECORD=1 uv run --directory daemon pytest -m real_agent   # also re-record
```

The Codex real run (`tests/services/agents/test_codex_real_run.py`) uses the installed `codex` and is skipped unless `SPOOLHQ_REAL_BACKENDS` lists `codex` and `codex login status` succeeds:

```sh
SPOOLHQ_REAL_BACKENDS=codex uv run --directory daemon pytest -m real_agent
```

On 2026-10-31 with Codex 0.166.0 and a ChatGPT login it passed in about 6 s: one turn, 35,872 input tokens (23,424 cached) and 246 output, 15,036 weighted.

## `spool agents`

Lists the detected backends (with `--project <name>`, the roles instead; see [roles](#roles-and-backends)). For Codex it also shows, per role, which policy parts it enforces here:

```text
claude-code-cli
  installed  yes (2.1.302)
  login      yes (claude.ai, subscription)
  policy     yes (enforceable)

codex-cli
  installed  yes (0.166.0)
  login      yes (chatgpt, subscription)
  policy     yes (enforceable)
  planner      read-only yes, approvals never asked yes, network off yes, denied reads yes, the shell allowlist yes
  implementer  writes confined to the worktree yes, approvals never asked yes, network off yes, denied reads yes, the shell allowlist yes
  reviewer     read-only yes, approvals never asked yes, network off yes, denied reads yes, the shell allowlist yes
```

For the Agent SDK it shows the SDK and Claude Code versions, whether a key is set (never the key) and the parts per role:

```text
claude-agent-sdk
  installed  yes (0.2.176, bundled Claude Code 2.1.316)
  login      yes (api key from keychain, api)
  policy     yes (enforceable)
  planner      read-only yes, approvals never asked yes, network off yes, denied reads yes, the shell allowlist yes
  implementer  writes confined to the worktree yes, approvals never asked yes, network off yes, denied reads yes, the shell allowlist yes
  reviewer     read-only yes, approvals never asked yes, network off yes, denied reads yes, the shell allowlist yes
```

Without a key the login line reads `no (run: spool secrets set anthropic)`.

It exits 0 even when nothing is installed; the output then says how to install each CLI and log in (`claude auth login`, `codex login`).

## Known limits

- **Codex: permission profiles are beta**, and Codex sends no `init`-like message, so SpoolHQ can't check up front that the profile took effect; it relies on the refusals above and stops a run whose stream shows a turned-off tool or a read-only file change. Codex's denials are recognised from command output, best effort.
- **Codex itself may write under `CODEX_HOME`** (refreshing its login, its own state); SpoolHQ never does.

- **Sandboxed commands can still read files not on the deny list.** The sandbox restricts writes and network, not reads in general; a test the agent writes can read other files in your home folder. It cannot send them anywhere (no network) or write them outside the worktree and the temp folder, but it could copy them into the worktree, where they would end up in the diff. Docker isolation (later phase) closes this.
- **`files_changed` comes from the file tools.** A file changed by a command (`just install` writing a lockfile, a code generator) is not in it; the run loop takes the files changed from git instead.
- **Scrub stubs at the top of the worktree.** During a run the placeholders above exist in the worktree (Claude Code probably uses them to write-protect those files for sandboxed commands; not verified). An agent that legitimately creates one of these as an empty file loses it at cleanup.
- **The temp folder is writable.** Sandboxed commands may write to the system temp folder, which other processes can read.
- Claude Code's `permission_denied` messages are best-effort; the result's `permission_denials` is the complete list, and the parser reports a denial found only there too.
