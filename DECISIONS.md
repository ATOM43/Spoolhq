# Decisions

Read this index, then open only the area files your ticket touches. Each line is `number · title · area file`; the entry, with its reason, is in the area file.

Adding a decision: append it to the bottom of its area file, numbered after the highest number here, then add its line at the bottom of this index. To change a decision, add a new one that supersedes it. `just lint` (`scripts/check_decisions.py`) checks that the two agree.

001 · Name: SpoolHQ · docs/decisions/core.md
002 · UI: Tauri 2 + React + TypeScript. · docs/decisions/desktop.md
003 · Separate Python daemon (FastAPI). · docs/decisions/core.md
004 · CLI: Typer. · docs/decisions/core.md
005 · Agent runtime: Claude Agent SDK behind an `AgentRunner` interface. · docs/decisions/agents.md
006 · Storage: files for projects and tickets, SQLite for run history. · docs/decisions/core.md
007 · Stack templates: Copier. · docs/decisions/projects-tickets.md
008 · Only the planner, implementer and reviewer are LLM agents; everything else is plain code. · docs/decisions/agents.md
009 · Local git first, GitHub optional. · docs/decisions/git-github.md
010 · Licence: Apache-2.0. · docs/decisions/core.md
011 · TypeScript pinned to 6.0.3, not 7.x. · docs/decisions/desktop.md
012 · `.gitattributes` forces LF line endings. · docs/decisions/core.md
013 · ruff's `S` (security) rules are on. · docs/decisions/core.md
014 · `uv sync --locked` everywhere. · docs/decisions/core.md
015 · The justfile's Windows shell is `powershell.exe`, not `pwsh`. · docs/decisions/core.md
016 · The GitHub repo is `ATOM43/spoolhq`. · docs/decisions/git-github.md
017 · The daemon binds to 127.0.0.1 only, with no override. · docs/decisions/core.md
018 · Local auth is a bearer token in `~/.spoolhq/token` (mode 0600, folder 0700). · docs/decisions/core.md
019 · `GET /api/health` needs no token. · docs/decisions/core.md
020 · Requests whose `Host` is not `127.0.0.1:<port>` or `localhost:<port>` get 400. · docs/decisions/core.md
021 · Logs are JSON lines from stdlib `logging` with a small formatter, no logging dependency. · docs/decisions/core.md
022 · Runtime dependencies are pinned exactly in `pyproject.toml`, like the dev tools. · docs/decisions/core.md
023 · The CLI's HTTP client ignores proxy environment variables (`trust_env=False`). · docs/decisions/api.md
024 · The daemon token stays in Rust. · docs/decisions/desktop.md
025 · No HTTP plugin; the scope lives in the command. · docs/decisions/desktop.md
026 · Strict CSP. · docs/decisions/desktop.md
027 · Settings uses the native `<dialog>`, not Radix Dialog. · docs/decisions/desktop.md
028 · Fonts are bundled with `@fontsource`, no CDN. · docs/decisions/desktop.md
029 · shadcn/ui components use SpoolHQ's token names · docs/decisions/desktop.md
030 · Status rules. · docs/decisions/desktop.md
031 · The app reads the port like the daemon: · docs/decisions/desktop.md
032 · Rust is pinned like the rest: · docs/decisions/desktop.md
033 · `@tanstack/react-query` is pinned to 5.104.3, not 5.104.4. · docs/decisions/desktop.md
034 · Backend layering: `core` → `services` → `api`/`cli`, enforced by import-linter. · docs/decisions/core.md
035 · Frontend: Feature-Sliced Design, enforced by lint. · docs/decisions/desktop.md
036 · `core/logs.py` keeps its name · docs/decisions/core.md
037 · Design tokens live in `shared/styles/tokens.css`; · docs/decisions/desktop.md
038 · `unrs-resolver`'s install script is not run · docs/decisions/desktop.md
039 · `project.yaml` is read and written with ruamel.yaml in round-trip mode. · docs/decisions/projects-tickets.md
040 · `spool init` builds the workspace in a temp folder next to the target and renames it into place. · docs/decisions/projects-tickets.md
041 · Project names are slugs: `^[a-z0-9][a-z0-9-]{0,62}$`, checked with `fullmatch`. · docs/decisions/projects-tickets.md
042 · CLI commands for local file operations call services directly; the daemon is not needed. · docs/decisions/projects-tickets.md
043 · `repo` in `project.yaml` must be an absolute path or start with `~`. · docs/decisions/projects-tickets.md
044 · 85% line-coverage floor on the daemon, enforced in CI · docs/decisions/core.md
045 · A ticket's body is kept as the exact original text and never re-rendered. · docs/decisions/projects-tickets.md
046 · Saving a ticket rewrites only the frontmatter lines of keys that changed. · docs/decisions/projects-tickets.md
047 · The editor for `spool tickets edit` runs as an argument list. · docs/decisions/projects-tickets.md
048 · Ticket frontmatter is validated in Pydantic's strict mode. · docs/decisions/projects-tickets.md
049 · `spool tickets edit` keeps its backup as a hidden `tickets/.<file>.bak` · docs/decisions/projects-tickets.md
050 · Round-trip fixtures are marked `-text` in `.gitattributes` · docs/decisions/projects-tickets.md
051 · `git.remote` follows GitHub's naming rules. · docs/decisions/git-github.md
052 · The transition table in `services/scheduler/transitions.py` is the only source of truth for status changes. · docs/decisions/projects-tickets.md
053 · Setting the status a ticket already has is a no-op, not an error. · docs/decisions/projects-tickets.md
054 · Ties on the critical path go to the lower ticket ids, compared from the start of the chain, and hours are summed as decimals. · docs/decisions/projects-tickets.md
055 · The scheduler refuses an invalid plan. · docs/decisions/projects-tickets.md
056 · Cycles are found by a depth-first walk in id order, one cycle per back edge, each rotated to start at its lowest id. · docs/decisions/projects-tickets.md
057 · Arrows in plan output point in work order · docs/decisions/projects-tickets.md
058 · CLI forces UTF-8 on stdout/stderr. · docs/decisions/core.md
059 · Run history is stdlib `sqlite3` in WAL mode with `synchronous=NORMAL`, no ORM. · docs/decisions/runloop.md
060 · Schema migrations are an ordered list of SQL scripts tracked by `PRAGMA user_version`. · docs/decisions/runloop.md
061 · Events are append-only, enforced by triggers. · docs/decisions/runloop.md
062 · Attempt numbers count per ticket across all its runs, and each attempt has its own folder `runs/<ticket>/<NNN>/`. · docs/decisions/runloop.md
063 · Cost is stored as integer micro-USD (`cost_micro_usd`). · docs/decisions/runloop.md
064 · The event bus is synchronous and bounded, with lag-and-resync instead of back-pressure. · docs/decisions/runloop.md
065 · Persist before publish. · docs/decisions/runloop.md
066 · Crash recovery is by daemon instance, made safe by a single-instance lock. · docs/decisions/runloop.md
067 · Recovery touches only the database. · docs/decisions/runloop.md
068 · `spool runs` reads `state.db` directly, read-only. · docs/decisions/runloop.md
069 · An empty attempt folder left by an attempt that never committed is reused. · docs/decisions/runloop.md
070 · The daemon finds workspaces with `list_workspaces(projects_dir)` · docs/decisions/projects-tickets.md
071 · One worktree per run, not per attempt. · docs/decisions/git-github.md
072 · SpoolHQ owns only the branches it marked. · docs/decisions/git-github.md
073 · A new worktree needs a strictly clean main repository, untracked files included. · docs/decisions/git-github.md
074 · SpoolHQ's own commits use `--no-verify`. · docs/decisions/git-github.md
075 · No fetch or push until T17. · docs/decisions/git-github.md
076 · git 2.36 or newer. · docs/decisions/git-github.md
077 · Startup recovery keeps the worktrees of blocked and awaiting-approval runs. · docs/decisions/git-github.md
078 · Ticket status reconciliation is still owed by T13. · docs/decisions/git-github.md
079 · The ticket id pattern moved to `core/ids.py`. · docs/decisions/core.md
080 · The worktree root is a setting, `worktrees_dir` · docs/decisions/git-github.md
081 · `run_git` also removes `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` and the other repository-location variables, and gives git an empty stdin. · docs/decisions/git-github.md
082 · Commits run with `user.useConfigOnly=true`. · docs/decisions/git-github.md
083 · Only entries named like a ticket id, directly under `<root>/<project>/`, are SpoolHQ's. · docs/decisions/git-github.md
084 · SpoolHQ's git calls never run repository hooks. · docs/decisions/git-github.md
085 · SpoolHQ's git calls never sign. · docs/decisions/git-github.md
086 · A Graphify code graph is committed in `graphify-out/` for agent context. · docs/decisions/codegraph.md
087 · Daemon tests mirror the source layout. · docs/decisions/core.md
088 · The agent policy is enforced by Claude Code, in four layers; SpoolHQ builds the configuration and verifies it took effect. · docs/decisions/agents.md
089 · The allowlist is the project's stack commands plus read-only git, two rules per command. · docs/decisions/agents.md
090 · The OS sandbox is required. · docs/decisions/agents.md
091 · No network for the agent's commands in v1 · docs/decisions/agents.md
092 · Sandboxed commands may not read the usual credential files or the SpoolHQ home: · docs/decisions/agents.md
093 · The `claude` process gets only an allowlisted environment. · docs/decisions/agents.md
094 · The prompt goes on stdin, never as an argument. · docs/decisions/agents.md
095 · A usage limit is an outcome, not a failure. · docs/decisions/agents.md
096 · Cost and tokens. · docs/decisions/agents.md
097 · Claude Code 2.1.259 or newer. · docs/decisions/agents.md
098 · The adapter also accepts the `default` permission mode in `init`. · docs/decisions/agents.md
099 · The `init` message is checked before anything else is believed. · docs/decisions/agents.md
100 · `Glob` and `Grep` are in `--tools` and `--allowedTools`, and the settings include `disableAllHooks: true`. · docs/decisions/agents.md
101 · `FileEdit` comes from a successful tool result, not the tool call. · docs/decisions/agents.md
102 · A worktree must not contain the user's home, the SpoolHQ home or a denied path, or sit inside one. · docs/decisions/agents.md
103 · `ClaudeCliRunner`'s `platform` parameter only changes `detect()`'s sandbox rules. · docs/decisions/agents.md
104 · SpoolHQ cleans up after Claude Code's env scrub. · docs/decisions/agents.md
105 · Prompts are Jinja2 templates in a `SandboxedEnvironment` · docs/decisions/runloop.md
106 · Untrusted text is only ever a template variable, never template source. · docs/decisions/runloop.md
107 · Every untrusted input sits in its own tag block, and its closing tag is escaped inside it. · docs/decisions/runloop.md
108 · The default template is package data · docs/decisions/runloop.md
109 · Prompt overrides live in the workspace, `<workspace>/prompts/implementer.md.j2`, · docs/decisions/runloop.md
110 · The prompt budget counts characters, not tokens: · docs/decisions/runloop.md
111 · The progress note comes back in the agent's final message, · docs/decisions/runloop.md
112 · The prompt is deterministic and machine-neutral: · docs/decisions/runloop.md
113 · Trim order and caps: · docs/decisions/runloop.md
114 · The previous attempt comes first after the rules, before the ticket, · docs/decisions/runloop.md
115 · `services/context` keeps its own copy of the read-only git commands · docs/decisions/runloop.md
116 · `RenderedPrompt.cuts` prefixes each note with its file · docs/decisions/runloop.md
117 · When a block's measured overhead is a few characters off after a cut · docs/decisions/runloop.md
118 · Supersedes 5: agents run through the Claude Code CLI (see 88), · docs/decisions/agents.md
119 · Supersedes the keep rule of 77: startup recovery also keeps the worktrees of interrupted runs. · docs/decisions/git-github.md
120 · Claude Code's own files are denied to sandboxed commands: · docs/decisions/agents.md
121 · `default_branch` must be a branch name, not any revision. · docs/decisions/git-github.md
122 · Each workspace's event bus starts at the database's last event id. · docs/decisions/runloop.md
123 · `RunResult.summary` keeps the end of the agent's final message, · docs/decisions/agents.md
124 · The `claude` environment also passes the lower-case proxy variables, `NODE_EXTRA_CA_CERTS` and `SSL_CERT_FILE` · docs/decisions/agents.md
125 · `spool serve` has no `--port` option; · docs/decisions/core.md
126 · Shared helpers have one copy: · docs/decisions/core.md
127 · No source file over 500 lines. · docs/decisions/core.md
128 · Gates never use a shell. · docs/decisions/runloop.md
129 · Gates get a scrubbed environment: · docs/decisions/runloop.md
130 · Known gap: gates have no filesystem isolation yet. · docs/decisions/runloop.md
131 · Install → lint → test. · docs/decisions/runloop.md
132 · Timeouts and stopping. · docs/decisions/runloop.md
133 · Output is cleaned and capped while it streams. · docs/decisions/runloop.md
134 · The excerpt keeps the first failure: · docs/decisions/runloop.md
135 · The first failure line · docs/decisions/runloop.md
136 · Failing test names are extracted deterministically, · docs/decisions/runloop.md
137 · "Done when" items run nothing. · docs/decisions/runloop.md
138 · `services/gates` returns T10-shaped plain data instead of importing `services/context`. · docs/decisions/runloop.md
139 · The reviewer gets a fresh context, enforced by types. · docs/decisions/runloop.md
140 · The reviewer's tools are read-only. · docs/decisions/runloop.md
141 · The verdict comes back as a `<verdict>{…}</verdict>` block at the end of the final message; the last block wins, and JSON in a code fence inside it is accepted. · docs/decisions/runloop.md
142 · The verdict schema is strict. · docs/decisions/runloop.md
143 · Items the gates checked take the gates' answer, and consistency is checked after merging. · docs/decisions/runloop.md
144 · Invalid output is retried once, with the errors and never the previous output. · docs/decisions/runloop.md
145 · Run outcomes other than `completed` are passed through. · docs/decisions/runloop.md
146 · The reviewer's untrusted input sits in four escaped tag blocks: · docs/decisions/runloop.md
147 · The diff is capped at 150,000 characters. · docs/decisions/runloop.md
148 · Reviewer budget defaults: · docs/decisions/runloop.md
149 · The reviewer's template is `services/context/prompts/reviewer.md.j2`, · docs/decisions/runloop.md
150 · "Done when" parsing stays in `services/tickets/checklist.py`. · docs/decisions/runloop.md
151 · `FakeRunner` accepts a sequence of transcripts · docs/decisions/agents.md
152 · `spool review` runs no gates. · docs/decisions/runloop.md
153 · Note for T13: · docs/decisions/runloop.md
154 · The daemon owns the run loop. · docs/decisions/runloop.md
155 · One run per project · docs/decisions/runloop.md
156 · One worktree per run; retries are new attempts in the same worktree · docs/decisions/runloop.md
157 · SpoolHQ commits, not the agent. · docs/decisions/runloop.md
158 · Files changed come from git · docs/decisions/runloop.md
159 · The state machine · docs/decisions/runloop.md
160 · Retry counters are read from the attempt rows, not kept in memory · docs/decisions/runloop.md
161 · The retry prompt's previous attempt is read from the last finished attempt's files · docs/decisions/runloop.md
162 · Integration is a seam. · docs/decisions/runloop.md
163 · Every step is recorded in the run log · docs/decisions/runloop.md
164 · Run log schema version 2 · docs/decisions/runloop.md
165 · Usage limits pause, never block. · docs/decisions/runloop.md
166 · Other agent outcomes: · docs/decisions/runloop.md
167 · Budget per ticket · docs/decisions/runloop.md
168 · Cancel · docs/decisions/runloop.md
169 · Crash recovery: · docs/decisions/runloop.md
170 · Daemon shutdown leaves runs for recovery. · docs/decisions/runloop.md
171 · `run all` · docs/decisions/runloop.md
172 · Init permission mode `default` is accepted only when it is really safe · docs/decisions/agents.md
173 · Event bus listeners stay cheap: · docs/decisions/runloop.md
174 · `spool run` takes the project as its first argument · docs/decisions/runloop.md
175 · The run endpoints live in `api/routers/runs.py` · docs/decisions/api.md
176 · A project created after the daemon started gets its run log on first use · docs/decisions/runloop.md
177 · The default branch is only ever fast-forwarded; nothing is rebased or merged on it. · docs/decisions/runloop.md
178 · Advancing main is a compare-and-swap. · docs/decisions/runloop.md
179 · A dirty main checkout never blocks the ticket; integration waits. · docs/decisions/runloop.md
180 · Conflicts go back to the implementer once. · docs/decisions/runloop.md
181 · The gates rerun only when the merge-in brought something, with T13's gate-retry rules. · docs/decisions/runloop.md
182 · The squash commit is built on a detached `HEAD` in the worktree. · docs/decisions/runloop.md
183 · Commit message. · docs/decisions/runloop.md
184 · `PROGRESS.md` is updated in the squash commit. · docs/decisions/runloop.md
185 · Each merged ticket gets a lightweight tag `ticket/<id>`. · docs/decisions/runloop.md
186 · The diff guard runs on the staged squash (`git diff --cached --name-only <main_sha>`), case-insensitively. · docs/decisions/runloop.md
187 · The integration journal is schema version 3, not 2. · docs/decisions/runloop.md
188 · Startup recovery of the journal runs after the run log's recovery and before T08's worktree recovery. · docs/decisions/runloop.md
189 · The integrator closes the run itself. · docs/decisions/runloop.md
190 · `spool run integrate <project> <ticket>` · docs/decisions/runloop.md
191 · Hold mode is `run.integration: hold` in `project.yaml` · docs/decisions/runloop.md
192 · T10's retry note is split into `user_note` and `system_note` · docs/decisions/runloop.md
193 · The event kind is `integrate` · docs/decisions/runloop.md
194 · A git error mid-squash restores the worktree. · docs/decisions/runloop.md
195 · The implementer may not run the project's `install` command · docs/decisions/agents.md
196 · The diff guard also drops `.pnpm-store/`, `.npm/` and `.yarn/cache/` · docs/decisions/runloop.md
197 · An added or changed symlink whose target is absolute (POSIX or Windows) or leaves the repo blocks the ticket · docs/decisions/runloop.md
198 · The reviewer judges only the committed diff. · docs/decisions/runloop.md
199 · SpoolHQ's own `.gitignore` ignores `.pnpm-store/`. · docs/decisions/core.md
200 · `spool run status` takes the last merged ticket from the integration journal · docs/decisions/runloop.md
201 · Agents started by SpoolHQ don't edit `PROGRESS.md`. · docs/decisions/runloop.md
202 · The per-ticket token budget counts weighted tokens · docs/decisions/agents.md
203 · The implementer prompt asks for fewer, larger turns · docs/decisions/runloop.md
204 · The prompt takes only the newest history · docs/decisions/runloop.md
205 · `npm_config_verify_deps_before_run=false` is in `ENV_SET`. · docs/decisions/agents.md
206 · The planner is read-only · docs/decisions/projects-tickets.md
207 · Planner inputs: · docs/decisions/projects-tickets.md
208 · Planning rules: · docs/decisions/projects-tickets.md
209 · The planner ends with one `<plan>` JSON block, validated in code: · docs/decisions/projects-tickets.md
210 · "New ids continue from the highest existing number" means: · docs/decisions/projects-tickets.md
211 · Missing test-command item is appended, not refused. · docs/decisions/projects-tickets.md
212 · Draft files: · docs/decisions/projects-tickets.md
213 · Edit detection by hash: · docs/decisions/projects-tickets.md
214 · All-or-nothing writes: · docs/decisions/projects-tickets.md
215 · Invalid ticket files stop the planner · docs/decisions/projects-tickets.md
216 · `spool plan generate|show|approve` run locally · docs/decisions/projects-tickets.md
217 · Plan runs in the run log: · docs/decisions/projects-tickets.md
218 · The API runs the planner in `PlanJobs` · docs/decisions/projects-tickets.md
219 · The planner's budget is `agents.budget_per_ticket.tokens` over both attempts together · docs/decisions/projects-tickets.md
220 · The dashboard plan fixture uses 1.5 h for T01 and T02 · docs/decisions/projects-tickets.md
221 · Copier is the template engine · docs/decisions/projects-tickets.md
222 · Templates get no trust. · docs/decisions/projects-tickets.md
223 · The contract is `spoolhq-template.yaml` · docs/decisions/projects-tickets.md
224 · Sources: · docs/decisions/projects-tickets.md
225 · `spool init --template` refuses anything but a missing or empty `--repo` · docs/decisions/projects-tickets.md
226 · `project.yaml`'s `template` is now a block · docs/decisions/projects-tickets.md
227 · `services.templates` may import `services.projects`, `services.gates` and `services.git`. · docs/decisions/projects-tickets.md
228 · The contract check · docs/decisions/projects-tickets.md
229 · `fastapi-react` pins (2026-10-25): · docs/decisions/projects-tickets.md
230 · `fastapi-react` structure choices: · docs/decisions/projects-tickets.md
231 · The built-in template is excluded from SpoolHQ's ruff and mypy · docs/decisions/projects-tickets.md
232 · `fastapi-react`'s justfile exports `PYTHONUTF8=1`. · docs/decisions/projects-tickets.md
233 · SpoolHQ clones git-URL templates and hands Copier a plain folder (supersedes the clone part of 221–231). · docs/decisions/projects-tickets.md
234 · The `fastapi-react` template uses `httpx` 0.28.1 again, not `httpx2` (supersedes the `httpx2` pin in 229). · docs/decisions/projects-tickets.md
235 · GitHub delivery is chosen per project and per ticket (T17). · docs/decisions/git-github.md
236 · Git auth is the user's own git setup; SpoolHQ fetches by URL. · docs/decisions/git-github.md
237 · Push before local main moves. · docs/decisions/git-github.md
238 · A failed fetch blocks; recovery that can't fetch waits. · docs/decisions/git-github.md
239 · The GitHub token: environment, then the OS keychain (T17). · docs/decisions/git-github.md
240 · Pull request text is escaped, not sanitised. · docs/decisions/git-github.md
241 · The run stores its pull request's number, URL and branch (schema 6). · docs/decisions/git-github.md
242 · Changes requested continue the same run. · docs/decisions/git-github.md
243 · Polling runs in the daemon process, and in its own module. · docs/decisions/git-github.md
244 · What a merged PR does to local main. · docs/decisions/git-github.md
245 · Failures around a pull request. · docs/decisions/git-github.md
246 · A local template folder that is a git repository is cloned like a git URL (T18 step 0; closes the follow-up in 233). · docs/decisions/projects-tickets.md
247 · Remote git calls run ssh in batch mode. · docs/decisions/git-github.md
248 · The merge policy is pure and records every hit (T18). · docs/decisions/runloop.md
249 · The policy runs on the staged squash, before the commit and before the `PROGRESS.md` entry. · docs/decisions/runloop.md
250 · A `needs_human` verdict is integrated like an approval and the policy sends it to a person. · docs/decisions/runloop.md
251 · Hold mode is a policy rule (`hold_mode`), not a separate integrator. · docs/decisions/runloop.md
252 · Approval is recorded per attempt, in the run log. · docs/decisions/runloop.md
253 · Reject reuses `pr_changes`. · docs/decisions/runloop.md
254 · The run row stores the latest decision as JSON (`runs.policy`, schema 7), written with its `policy.decision` event in one transaction · docs/decisions/runloop.md
255 · `merge_policy` settings follow the ticket, not T04's placeholder. · docs/decisions/runloop.md
256 · PR-mode token check moved after the squash. · docs/decisions/runloop.md
257 · Roles resolve through a backend registry · docs/decisions/agents.md
258 · `services/projects` imports `services/agents` · docs/decisions/agents.md
259 · Custom endpoints: `agents.backends.<name>.base_url` and `.model` · docs/decisions/agents.md
260 · One contract suite over adapter cases · docs/decisions/agents.md
261 · A custom endpoint gets SpoolHQ's own token, never the subscription login · docs/decisions/agents.md
262 · Codex CLI is the `codex-cli` backend, on the T09 contract · docs/decisions/agents.md
263 · The policy goes in a per-run permission profile, not `--sandbox` · docs/decisions/agents.md
264 · How Codex enforces each part · docs/decisions/agents.md
265 · No per-command allowlist in Codex; its sandbox stands in for the implementer · docs/decisions/agents.md
266 · Refuse, per role, what Codex can't enforce here · docs/decisions/agents.md
267 · Per-run settings without a per-run `CODEX_HOME` · docs/decisions/agents.md
268 · Codex's environment · docs/decisions/agents.md
269 · Codex's custom endpoint · docs/decisions/agents.md
270 · Codex usage, limits and denials · docs/decisions/agents.md
271 · One process session for both CLIs · docs/decisions/agents.md
272 · Terms check: unclear · docs/decisions/agents.md
273 · Warn, don't refuse, for a Codex reviewer or planner · docs/decisions/agents.md
274 · Real Codex 0.166.0 findings · docs/decisions/agents.md
275 · Refuse Codex in a worktree under a shared temp folder · docs/decisions/agents.md
276 · Plan: Gemini dropped, T31 is the Agent SDK only · docs/decisions/agents.md
277 · The Claude Agent SDK is the `claude-agent-sdk` backend, on the T09 contract · docs/decisions/agents.md
278 · SpoolHQ gives the SDK its own `Transport` · docs/decisions/agents.md
279 · API key only, never a subscription login · docs/decisions/agents.md
280 · The policy per role, twice: Claude Code's options and a `PreToolUse` hook · docs/decisions/agents.md
281 · Cost, the USD budget and billing errors · docs/decisions/agents.md
282 · Testing the SDK backend with the real SDK client and a fake CLI · docs/decisions/agents.md
283 · Starlette's `TestClient` answers with `httpx2` once it is installed · docs/decisions/core.md
284 · Plan: the code graph ticket is T28 · docs/decisions/codegraph.md
285 · The flaky Agent SDK run-loop test was a fixture race, fixed in the fixture · docs/decisions/agents.md
286 · What Graphify 0.9.92 offers, checked rather than remembered · docs/decisions/codegraph.md
287 · The code graph: optional, offline, one cache per project · docs/decisions/codegraph.md
288 · When the map is built · docs/decisions/codegraph.md
289 · The code map in the prompt · docs/decisions/codegraph.md
290 · SpoolHQ never commits a graph · docs/decisions/codegraph.md
291 · A line the Agent SDK can't parse is skipped, not fatal · docs/decisions/agents.md
292 · Tracked files in build folders are committed · docs/decisions/codegraph.md
293 · The Windows subprocess environment was already complete · docs/decisions/agents.md
294 · `spool prompt show` says the map is missing · docs/decisions/codegraph.md
295 · Route inventory and renames · docs/decisions/api.md
296 · One error format, with stable codes · docs/decisions/api.md
297 · ETags: a per-project in-process lock, not an OS file lock · docs/decisions/api.md
298 · Unblock continues the blocked run · docs/decisions/api.md
299 · Paging by `(started_at, id)` · docs/decisions/api.md
300 · The WebSocket checks the token itself · docs/decisions/api.md
301 · How events reach a socket, and the threading rule · docs/decisions/api.md
302 · Closing with 1001 on shutdown · docs/decisions/api.md
303 · The TypeScript client goes through Rust, and the WebSocket token comes from the caller · docs/decisions/api.md
304 · The generated files · docs/decisions/api.md
305 · Secrets · docs/decisions/api.md
306 · Plan: T20 split into T20 and T32 · docs/decisions/desktop.md
307 · Events go through Rust, so the CSP is unchanged · docs/decisions/desktop.md
308 · The Rust WebSocket crate · docs/decisions/desktop.md
309 · The folder picker is Tauri's dialog plugin · docs/decisions/desktop.md
310 · Run events invalidate queries, coalesced · docs/decisions/desktop.md
311 · Trying a stack command is project-scoped, after creation · docs/decisions/api.md
312 · Home's states · docs/decisions/desktop.md
313 · Subscribing from the latest event · docs/decisions/desktop.md
314 · The frontend file-length limit already existed · docs/decisions/core.md
315 · The daemon says what can run · docs/decisions/api.md
316 · Panel state and the tab it opens on · docs/decisions/desktop.md
317 · Disabled controls carry their reason · docs/decisions/desktop.md
318 · Spec autosave · docs/decisions/desktop.md
319 · Generate plan, Re-plan and failures · docs/decisions/desktop.md
320 · Markdown renderer · docs/decisions/desktop.md
321 · Settings · docs/decisions/desktop.md
322 · The daemon ships a WebSocket library · docs/decisions/api.md
323 · An invalid `project.yaml` is reported, not raised · docs/decisions/api.md
324 · Usage, last activity and the run's step come from the run log · docs/decisions/runloop.md
325 · "No spec yet" means blank or untouched · docs/decisions/projects-tickets.md
326 · Project status, most urgent first · docs/decisions/desktop.md
327 · Disabled controls look disabled, with a CSS-only tooltip · docs/decisions/desktop.md
328 · Home and Needs you · docs/decisions/desktop.md
329 · Where the spec won over the PNGs · docs/decisions/desktop.md
330 · Agent docs are split: an index plus area files · docs/decisions/core.md
331 · The context pack expands a decisions index · docs/decisions/runloop.md
332 · Settings opens from anywhere, and "set up an agent" links to it · docs/decisions/desktop.md
333 · Settings layout and secret tests · docs/decisions/desktop.md
334 · Where the spec won over the D2 PNG · docs/decisions/desktop.md
335 · Testing a secret · docs/decisions/api.md
336 · `PLW1514` is on, and `just lint` checks `scripts/` · docs/decisions/core.md
337 · Project creation is a job that rolls back only what it created · docs/decisions/projects-tickets.md
338 · A new project's repo path is untrusted · docs/decisions/api.md
339 · Merge presets map onto the current `merge_policy` keys · docs/decisions/runloop.md
340 · The app polls a creation job · docs/decisions/api.md
341 · Stack commands are optional; without `test`, nothing plans or runs · docs/decisions/projects-tickets.md
342 · `spool init` runs the creation job, with built-in templates only · docs/decisions/projects-tickets.md
343 · Templates have a one-line `summary` · docs/decisions/projects-tickets.md
344 · The old New project dialog stays until T36 · docs/decisions/desktop.md
345 · `spool init` takes folder and git URL templates again; the API doesn't · docs/decisions/projects-tickets.md
346 · A project being created reports `creating`, and nothing else is read · docs/decisions/api.md
347 · The template list carries its commands, and the commands step its progress · docs/decisions/api.md
348 · The New project dialog · docs/decisions/desktop.md
349 · Where the spec won over the D1 PNG · docs/decisions/desktop.md
350 · A rollback that left paths behind is a list entry, `cleanup_failed` · docs/decisions/api.md
351 · The panel while a project is created, and error toasts · docs/decisions/desktop.md
352 · The plan summary is `GET …/plan`, and approve answers 409 `plan_invalid` · docs/decisions/api.md
353 · Listed tickets carry their run activity · docs/decisions/api.md
354 · The Tickets tab · docs/decisions/desktop.md
355 · The read-only ticket drawer · docs/decisions/desktop.md
356 · Where the spec won over the V2 and D4 PNGs · docs/decisions/desktop.md
357 · GitHub-style markdown · docs/decisions/desktop.md
358 · Rust files are under the 500-line limit, and Clippy denies long functions · docs/decisions/core.md
359 · The drawer reuses the existing ticket routes · docs/decisions/api.md
360 · The ticket detail carries the run, attempts and git · docs/decisions/api.md
361 · Unblock resets the retries with a log event · docs/decisions/runloop.md
362 · Ticket edits lock while a run owns the ticket, and refuse only what they introduce · docs/decisions/projects-tickets.md
363 · "Checked 20 s ago" is the poller's memory · docs/decisions/git-github.md
364 · Links are copied, not opened · docs/decisions/desktop.md
365 · The drawer's actions and edit mode · docs/decisions/desktop.md
366 · Where the spec won over the V2 and D3 PNGs · docs/decisions/desktop.md
367 · Tool results and edit line counts are agent events · docs/decisions/agents.md
368 · The implementer's transcript and the steps are run events · docs/decisions/runloop.md
369 · A run's events by attempt window, paged by seq · docs/decisions/api.md
370 · The Run tab's live events · docs/decisions/desktop.md
371 · Where the spec won over the V2 · Run tab, live PNG · docs/decisions/desktop.md
372 · A dev-only fake runner, `SPOOLHQ_DEV_FAKE_RUNNER` · docs/decisions/agents.md
373 · An attempt's reports are typed views over the stored files · docs/decisions/api.md
374 · Each gate starting is a `step` event with the gates done so far · docs/decisions/runloop.md
375 · The Run tab's Gates, Review and Diff panels · docs/decisions/desktop.md
376 · Where the spec won over the V2 PNGs · docs/decisions/desktop.md
377 · The run list carries the table's sums, and the events route its total · docs/decisions/api.md
378 · Past runs and replay · docs/decisions/desktop.md
379 · Where the spec won over the V2 · Run tab, idle PNG · docs/decisions/desktop.md
380 · A hand-added ticket gets the next number, and is Ready unless a draft plan waits · docs/decisions/projects-tickets.md
381 · `POST …/tickets` takes the form's fields, not `{meta, body}` · docs/decisions/api.md
382 · A ready ticket runs without a spec; the spec is needed only for Generate plan · docs/decisions/runloop.md
383 · Add ticket in the Tickets tab · docs/decisions/desktop.md
384 · The replay names the run and the attempt · docs/decisions/desktop.md
