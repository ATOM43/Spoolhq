# Daemon API

The daemon listens on `127.0.0.1` only (port 8765 unless `port` says otherwise). Every `/api/*` route needs the token from `~/.spoolhq/token` as `Authorization: Bearer <token>`, except `GET /api/health`; the event WebSocket takes it in its first message instead ([below](#event-websocket)). A request with a foreign `Host` header gets 400, a body over 1 MB gets 413.

The OpenAPI schema is at `/openapi.json` and `/docs` while the daemon runs. The desktop app's typed client is generated from it (see [TypeScript client](#typescript-client)).

## Endpoints

`{name}` is a project name (lowercase letters, digits and hyphens); `{id}` a ticket id, `T` and two or three digits. Both are checked by pattern before any route code runs (422 otherwise), so neither can become a path.

| Route | Does |
| --- | --- |
| `GET /api/health` | `{"status": "ok"}`, no token |
| `GET /api/version` | the daemon's version |
| `GET /api/projects` | each project: `name`, `done`/`total`/`draft` tickets, `remaining_h`, `run_state` (`running`, `paused`, `creating`, `cleanup_failed` or `idle`; see [A project being created](#a-project-being-created) and [Rollback](#rollback)), `needs_you` (tickets `awaiting_approval` or `blocked`), `latest_seq` (see [Starting from REST](#event-websocket)), `has_spec` (`CONTEXT.md` isn't blank or init's starter), `template` (null for an existing repo), `run` (the active, else latest run) and `run_step` (its latest phase), `last_activity` (the latest event's time), `usage` (`tokens` of attempts without a cost, `cost_usd` summed over those with one), and `settings_error` (`{file, field, message}`, the first problem of a `project.yaml` that doesn't load; the project is listed anyway) |
| `POST /api/projects` | start a [creation job](#creating-a-project), like `spool init`: 202 `{"job_id"}`, or 422 with the field before any job starts |
| `GET /api/jobs/{job_id}` | the creation job: `state` and its `steps`, plus `rollback` after a failure or cancel |
| `POST /api/jobs/{job_id}/cancel` | stop the job and roll back; answers when the rollback is done (at most 15 s) |
| `POST /api/jobs/{job_id}/dismiss` | 204: forget a job that ended, so the list stops showing what its rollback [left behind](#rollback); a running job stays |
| `POST /api/projects/{name}/commands/test` | `{"gate", "command"}`: run one stack command once in the project's repository, [as its gate would](#trying-a-stack-command) |
| `GET /api/projects/{name}` | the summary plus `repo`, `default_branch`, `remote` (all three null while `settings_error` is set), `invalid_tickets`, and what can run: `next_ticket` (what `run/next` would start, else null) and `idle` (`{code, ticket_ids, message}` when nothing can: `all_done`, `running`, `awaiting_approval`, `blocked`, `waiting`, `plan_not_approved` or `invalid_plan`; null with no tickets) |
| `GET`, `PUT /api/projects/{name}/settings` | `project.yaml` as `{"settings": {...}}`, validated by the project model; [ETag](#etags-and-edit-conflicts) |
| `GET`, `PUT /api/projects/{name}/spec` | `CONTEXT.md` as `{"content": "..."}`; ETag |
| `GET /api/projects/{name}/tickets?status=&phase=` | `{"tickets": [...], "invalid": [...]}`; each ticket is `id`, `file_name`, `meta` (the frontmatter), `body` and `activity` (null before its first run: `attempts`, `tokens` of attempts without a cost, `cost_micro_usd` summed over those with one, the latest run's `run_id` and `reason`) |
| `GET /api/projects/{name}/tickets/{id}` | one ticket (`activity` null) with its ETag and [what the drawer shows](#ticket-detail): `run`, `attempts`, `git` |
| `PUT /api/projects/{name}/tickets/{id}` | `{"meta", "body"}` with `If-Match`; see [Editing a ticket](#editing-a-ticket) |
| `POST /api/projects/{name}/tickets/{id}/unblock` | `{"note", "reset_retries"}`: continue a blocked ticket's run with a new attempt whose prompt has the note (`note` 1 character or more, else 422; `reset_retries` default true gives the run its full gate and review retries again; 409 `not_blocked`) |
| `POST /api/projects/{name}/tickets/{id}/approve` (`/integrate`), `/reject`, `/discard` | see [run-loop.md](run-loop.md#api-and-cli) |
| `GET /api/projects/{name}/plan` | the [plan summary](#plan-summary): `state`, `generated_at`, `ticket_count`, `total_h`, `problems` |
| `POST /api/projects/{name}/plan/generate`, `/plan/approve` | see [planner.md](planner.md#api); approve answers 409 `plan_invalid` with the problems while [any exist](#plan-summary) |
| `POST /api/projects/{name}/run/next`, `/run/all`, `/run/ticket/{id}` | start a run (201) |
| `POST /api/projects/{name}/run/pause`, `/run/resume`, `/run/cancel` | the current run (or `?run_id=`) |
| `GET /api/projects/{name}/runs/current` | the active (else latest) run with its phase lines, tokens and `cost_micro_usd` (null unless an API-key backend reported a cost), and `latest_seq` |
| `GET /api/projects/{name}/runs?cursor=&limit=` | the run history, [paged](#paged-run-history) |
| `GET /api/projects/{name}/runs/{run_id}` | one run with its `attempts` (number, kind, status — the verdict —, backend, tokens, times) |
| `GET /api/projects/{name}/runs/{run_id}/attempts/{n}/{artifact}` | an attempt's file as stored; `artifact` is `transcript`, `gates`, `diff` or `review` (422 for anything else) |
| `POST /api/projects/{name}/github/sync` | check open pull requests now |
| `GET /api/templates` | the built-in templates: `name` (what `POST /api/projects` takes as `template`), `description`, `summary` (one line of at most 120 characters, for a card; null if the template has none) and `commands` (`install`, `lint`, `test` from its `spoolhq-template.yaml`, which the New project dialog pre-fills) |
| `GET /api/agents` | what `spool agents` shows: each backend (installed, version, login, policy parts) and Graphify |
| `GET /api/settings` | the daemon's settings, and for each secret (`anthropic`, `github`, `clickup`) only `{"set", "source": "keychain" \| "env" \| null}` |
| `PUT`, `DELETE /api/settings/secrets/{name}` | store `{"value"}` in the OS keychain, or remove it (204) |
| `POST /api/settings/secrets/{name}/test` | [try the stored secret](#testing-a-secret) against its provider: `{"ok", "message"}` |
| `WS /api/projects/{name}/events?since=` | [live events](#event-websocket) |

An artifact is read from the attempt folder the run log names, by a fixed file name per `artifact`; the folder must resolve inside the workspace's `runs/`, and the file must not be a symlink and must resolve inside the folder, else 404.

A secret's value is write-only: it goes to the OS keychain (service `spoolhq`, through `keyring`) and is never returned, logged or written to a file. An environment variable (`ANTHROPIC_API_KEY`, `SPOOLHQ_GITHUB_TOKEN`, `SPOOLHQ_CLICKUP_TOKEN`) wins over the keychain, as it does where the secret is used. Without a usable keychain the answer is 409 `keychain_unavailable`.

## Creating a project

`POST /api/projects` takes:

| Field | |
| --- | --- |
| `name` | `^[a-z][a-z0-9-]{0,39}$` ("Use lowercase letters, digits and hyphens, starting with a letter"); no project of that name may exist |
| `source` | `template`, `existing` or `empty` |
| `repo_path` | absolute. `existing`: a git repository with a branch checked out and no uncommitted changes (they are listed); otherwise a folder that doesn't exist yet (its parent must) or is empty |
| `template` | `template` only: a name from `GET /api/templates`. No git URLs or local paths, since a Copier template can run code (`spool init` takes them; the request has no `template_ref` or `branch`) |
| `commands` | `install`, `lint`, `test`; each required unless `source` is `empty`, same no-shell rule as `project.yaml` |
| `git_remote`, `merge_preset`, `clickup_list_id` | optional; `merge_preset` is `direct_unless_risky` (default), `always_pr` or `always_direct` ([below](#merge-presets)) |

The path comes from the webview, so it is untrusted: it is resolved, and refused when it is the disk root, the home folder itself, inside the projects folder, the worktrees folder or `~/.spoolhq`, or a symlink. Every check runs before the job starts; a refusal is 422 with `field` (`name`, `repo_path`, `template`, `commands.test`, …) and no job.

The job then runs four steps, each `pending`, `running`, `passed`, `failed` or `skipped`, with `duration_s`:

1. **Create workspace** (`workspace`): `<projects>/<name>/` with `project.yaml`, the starter `CONTEXT.md`, `tickets/` and `runs/` (and `TEMPLATE.md` for a template).
2. **Prepare repo** (`repo`): Copier generates the template into `repo_path` (no trust, [templates](templates.md#no-trust)); `existing` is only checked again, never written to; `empty` creates the folder if needed and runs `git init -b main`.
3. **Check commands** (`commands`): install (600 s), then lint and test (300 s each), once each in the repo through the gates code (no shell, scrubbed environment). An unset command is skipped; with none the step is `skipped`. `passed` lists the commands that passed so far (the app shows "2 of 3 passed"). For `existing` they run in your checkout, as a gate would.
4. **Initial commit** (`commit`): `chore: generate from <template> <ref>` for a template, `git commit --allow-empty -m "Initial commit (SpoolHQ)"` for `empty` (hooks and signing off, your git identity required); skipped for `existing`.

A failed step has a fixed `message` ("The test command failed"), the trimmed `output` and the request `field` that caused it (`commands.test`, `repo_path`, `template`). The job's `state` is `running`, then `succeeded`, `failed` or `cancelled`. Jobs live in the daemon's memory for an hour after they end; a restart forgets them. The app polls `GET /api/jobs/{job_id}` every 500 ms only while a job runs, since no project event stream exists before the project does.

### A project being created

While a running job holds a project, `GET /api/projects` and `GET /api/projects/{name}` report it with `run_state: "creating"` and the job's `job_id`, and read nothing else: its `project.yaml` is written before the repo exists, so it is not validated (no `settings_error`), and the other fields keep their defaults (`needs_you` 0, no `run`). Home shows "Creating…", and the project panel shows the job's checklist instead of its tabs (it opens on Spec when the job succeeds, and says "This project wasn't created" when it fails or is cancelled). When the job ends the usual state takes over; a rolled-back project is gone from the list.

### Rollback

On a failure or cancel the job deletes exactly the paths it created, newest first, and records the result in `rollback`: `removed` (each deleted path) and `left` (any it couldn't delete; empty when the rollback is complete). It never deletes or changes anything that existed before: a folder that existed empty stays, emptied of what the job wrote, and an existing repository is never touched. Deleting never follows a symlink. The projects folder is removed only if the job created it and it is still empty.

While an ended job is kept (an hour) and its `left` isn't empty, `GET /api/projects` lists that project with `run_state: "cleanup_failed"`, the `job_id` and `left`, and nothing else (in place of its workspace, if that was left behind too). Home shows it as a Needs-you card, "Couldn't clean up <name>", with **Dismiss** (`POST /api/jobs/{job_id}/dismiss`); the app also shows a toast when a Cancel's rollback leaves something behind.

### Merge presets

Each preset is written as `project.yaml` [`merge_policy`](merge-policy.md) keys:

| Preset | `merge_policy` |
| --- | --- |
| `direct_unless_risky` | nothing written: the defaults |
| `always_pr` | `protected_paths: ['**']`: every change matches, so every ticket needs you (a pull request with a remote) |
| `always_direct` | `max_diff_lines: 100000`, `protected_paths: []`: the diff-size and protected-path rules are off; `review_required` and a reviewer's `needs_human` still send the ticket to you |

### Projects without commands

Stack commands are optional in `project.yaml`. Without a `test` command a project can't plan or run tickets: `run/next` and `plan/generate` answer 409 "Set the stack commands in project.yaml first", and the project detail's `idle` has code `no_commands` with that message.

## Plan summary

`GET /api/projects/{name}/plan` is what the Tickets tab's draft banner shows:

| Field | |
| --- | --- |
| `state` | `planning` while the planner runs in this daemon, else `draft` (any draft ticket), `approved` (tickets, none draft) or `none` (no tickets) |
| `generated_at` | when the planner last wrote the plan (`.spoolhq/plan.json`), or null |
| `ticket_count`, `total_h` | the drafts and their summed estimate while the plan is a draft (what approving moves), every ticket otherwise |
| `problems` | each `{code, message, ticket_ids}`, in this order: `invalid_ticket` (a file that doesn't load; `ticket_ids` from its file name), `unknown_dependency` (the ticket and the missing id), `cycle` (its members in work order, from the lowest id: `T07`, `T08`, `T09` for T07 → T08 → T09 → T07), `duplicate_id`, `missing_done_when` (a ticket that isn't done and has no "Done when" items) |

`POST …/plan/approve` checks the same problems first. With any, it answers 409 and changes no file:

```json
{"error": {"code": "plan_invalid", "message": "cannot approve the plan: cycle: T01 → T02 → T01", "problems": [{"code": "cycle", "message": "cycle: T01 → T02 → T01", "ticket_ids": ["T01", "T02"]}]}}
```

Without problems every draft becomes `ready` (200 `{"approved": [...]}`); with no drafts it is 409 `conflict` "nothing to approve".

## Testing a secret

Settings' **Test** button. `{name}` is `anthropic`, `github` or `clickup` (422 otherwise). The daemon reads the secret the way it uses it (environment first, then the keychain) and makes exactly one read-only HTTPS `GET`:

| Secret | Call |
| --- | --- |
| `anthropic` | `https://api.anthropic.com/v1/models` with `x-api-key` and `anthropic-version: 2023-06-01` |
| `github` | `https://api.github.com/user` with `Authorization: Bearer …` |
| `clickup` | `https://api.clickup.com/api/v2/user` with `Authorization: …` |

The URLs are fixed in the code (`services/secrets/check.py`); redirects are not followed and the timeout is 10 s. The answer is always 200 with `ok` and one fixed `message`: `Key works` (200), `Not set` (no call made), `Rejected (401)`, `Rejected (403)`, `Timed out`, `Couldn't reach <provider>` (no answer), or `Unexpected response (<status>)` (anything else, a redirect included). The secret, the provider's body and its headers never reach the answer; the log gets one line with the secret's name and the message. The result isn't stored.

## Trying a stack command

The New project dialog's **Test** button. The command is split with the gates' rules (`shlex`, no shell syntax: `&&`, `|`, `;`, redirects and `$(` are 422 with `field: "command"`), its program is looked up on the gates' scrubbed `PATH`, and it runs in the project's `repo` with the gates' environment (no secrets), stdin closed and a 90 s timeout that stops the whole process tree. It can change the checkout, as the gate would. The answer is `{"status": "passed" | "failed" | "timed_out" | "error", "exit_code", "duration_s", "output", "output_truncated", "timeout_s"}`; `output` is the trimmed excerpt the gates show (for `error`, why the program couldn't start). The 90 s stays below the desktop app's 120 s request timeout; a run still uses the project's own `gates.timeouts`.

## Errors

Every non-2xx answer has one shape:

```json
{"error": {"code": "edit_conflict", "message": "the file changed since you loaded it; reload and edit again", "field": null}}
```

`code` is snake_case and stable; `message` is for people; `field` names the offending input when there is one (`limit`, `cursor`, `meta.title`). Messages never repeat request values. Codes in use: `bad_request`, `bad_host`, `unauthorized`, `not_found`, `method_not_allowed`, `validation_error` (422), `conflict` (409, a refusal with the reason), `run_locked`, `not_blocked`, `invalid_transition`, `plan_invalid` (409, with `problems`), `template_error`, `keychain_unavailable`, `precondition_required` (428), `edit_conflict` (412), `payload_too_large` (413), `limit_too_large` and `invalid_cursor` (400).

## ETags and edit conflicts

Tickets, the spec and `project.yaml` carry an `ETag`: the quoted SHA-256 of the file's bytes, on every GET and after every successful PUT.

1. GET the file; keep its `ETag`.
2. PUT the edit with `If-Match: <that ETag>`. Without `If-Match` the answer is 428 `precondition_required`.
3. If the file changed in between (another client, `spool tickets edit`, an editor), the answer is 412 `edit_conflict` with the current `etag` and `current` content (as the GET returns it) inside `error`, and the file is left as it is. Show the user both, then PUT again with the new ETag.

The daemon reads the bytes, hashes and compares them, and writes (a temp file in the same folder, then `os.replace`), all under the project's edit lock, so two API edits never both win. Writers outside the daemon don't take that lock: an editor saving in the moment between the compare and the replace is overwritten. The window is a few milliseconds.

A ticket PUT goes through the ticket store, so only frontmatter keys whose value changed are rewritten and the body is kept byte for byte (an unchanged PUT writes the same bytes); a status change must be allowed by the scheduler's transition table (409 `invalid_transition`), and the id must still match the file name (422).

### Editing a ticket

A ticket can be edited while it is `draft`, `ready` or `blocked`; while it is `running` or `awaiting_approval` a PUT is 409 `ticket_locked` ("T05 is locked while running"). Only what the edit changes is checked, so an old ticket can still be fixed one part at a time; each refusal is 422 `validation_error` with the field, and nothing is written:

| Refused | `field` | Message |
| --- | --- | --- |
| a changed `depends_on` naming a ticket that doesn't exist | `meta.depends_on` | `T01 depends on T99, which does not exist` |
| a changed `depends_on` that makes a cycle through this ticket | `meta.depends_on` | `cycle: T01 → T03 → T01` |
| a changed body without "Done when" items | `done_when` | `“Done when” needs at least one checklist item` |

### Ticket detail

`GET …/tickets/{id}` adds what the ticket drawer shows to the ticket:

| Field | Meaning |
| --- | --- |
| `run` | the ticket's latest run (as `GET …/runs/{id}` has it, without attempts): `status`, `reason` (why it is blocked), `policy.rules` (the merge-policy rules that fired), `pr_number`, `pr_url` |
| `attempts` | every attempt of the ticket across its runs, oldest first, each with its `run_id` |
| `git.branch`, `git.commits`, `git.diff_lines` | the ticket's local `feat/<id>-…` branch while it exists, its commits ahead of the default branch and the lines they change; null without a branch |
| `git.commit`, `git.commit_url`, `git.tag` | the squash commit on the default branch once merged, that commit on GitHub (with a GitHub remote) and the `ticket/<id>` tag |
| `git.pr_number`, `git.pr_url`, `git.pr_state` | the latest run's pull request; `pr_state` is `open` (waiting), `merged` or `closed` |
| `git.pr_checked_at` | when this daemon last checked the project's open pull requests (null before the first check since it started) |

## Paged run history

`GET …/runs` returns runs newest first, `{"items": [...], "next_cursor": "..." | null}`. `limit` is 50 by default, at most 200 (400 `limit_too_large` above). Pass `next_cursor` back as `cursor` for the next page; it is `null` on the last page. The cursor is opaque (base64 of the last run's `started_at` and id); the next page holds the runs strictly older than it, so a run started while you page sorts before the cursor and never shows up twice.

## Event WebSocket

`ws://127.0.0.1:<port>/api/projects/{name}/events?since=<seq>`

**Auth.** A browser can't set headers on a WebSocket, and query strings end up in logs, so the client sends `{"type": "auth", "token": "..."}` as its first message, within 5 s. A wrong, missing or late token closes the socket with 4401 (compared with `hmac.compare_digest`).

**Origin.** A browser's `Origin` must be one of `allowed_origins` (setting; default the Tauri webview origins `tauri://localhost`, `http://tauri.localhost`, `https://tauri.localhost` and Vite's `http://localhost:1420`); any other is refused before the handshake completes (403). No `Origin` (a non-browser client) is allowed; the token still applies.

**Messages.** One envelope per event:

```json
{"seq": 812, "run_id": 14, "attempt": 3, "ticket": "T04", "type": "attempt.started", "ts": "2026-11-01T09:00:00.000Z", "data": {"number": 3, "kind": "gate_retry", ...}}
```

`seq` is the event's id in the run log; it only grows. `attempt` is the attempt's number (as in the artifact URL), `ticket` the run's ticket (`plan` for a plan run), `data` the event's payload; its shape per type is in the OpenAPI components (`RunStatusData`, `RunPhaseData`, `AttemptStartedData`, …). Payload text is untrusted. When nothing happens for 20 s the daemon sends `{"type": "ping"}`.

**Starting from REST.** `GET /api/projects`, `GET /api/projects/{name}` and `GET …/runs/current` include `latest_seq`: the newest stored event's `seq` (0 if none), read before the rest of the answer. A client loads its state over REST, then subscribes with `since=latest_seq`: it gets no history it already has, and an event written between the two calls still arrives, since the replay covers everything after `since`. The full history of a past run is read with `GET …/runs/{run_id}` and its artifacts, never by subscribing from 0.

**Replay without gaps or duplicates.** The daemon subscribes to the project's event bus first (new events queue up), then sends the stored events with `seq > since` from SQLite, then the queue, skipping anything at or below the last `seq` it sent, then stays live. Reconnect with `since=<last seq you saw>` and you get exactly what you missed.

**Close codes.**

| Code | Why | Client |
| --- | --- | --- |
| 4401 | bad, missing or late auth | stop; check the token |
| 4404 | unknown project | stop |
| 4408 `too_slow` | the client's queue (1,000 events) filled up | reconnect with `since` |
| 1001 | the daemon is shutting down | reconnect with backoff |
| 1008 / 403 | origin refused | stop |

**Threading rule.** The event bus calls its listener on whatever thread appended the event: the run loop's worker thread, a plan job's thread, or a request thread (approve, reject, unblock run in FastAPI's thread pool). The listener never awaits, blocks or touches the socket: it moves each event to the client's bounded `asyncio.Queue` with `loop.call_soon_threadsafe`, which works from any thread, the event loop's included. When a client's queue is full the daemon drops that client (4408) instead of waiting, so the run loop never waits on a client. `spool serve` closes the streams with 1001 when it is told to stop, before uvicorn's own shutdown would.

## TypeScript client

`just gen-api` dumps the schema without starting a server (`scripts/dump_openapi.py`) to `desktop/src/shared/api/openapi.json` and generates `schema.gen.ts` from it with `openapi-typescript`. `just lint` fails when either is stale: a pytest test compares the committed `openapi.json` with the daemon's, and `openapi-typescript --check` compares `schema.gen.ts`.

In `desktop/src/shared/api`:

- `api` (`http.ts`): an `openapi-fetch` client over `paths`. Each request goes through the Rust command `daemon_request`, which adds the token, so the token stays out of the webview. A non-2xx answer or a missing daemon rejects with a `DaemonError`; an API error is kind `api` with `code`, `message`, `field` and, for 412, `etag` and `current`.
- `subscribeEvents({ project, since, onStop }, onEvent)` (`events.ts`): the Rust command `events_subscribe` holds the socket. It sends the auth message, tracks the last `seq`, reconnects with `since` after a drop or a 4408 (backoff 0.5 s doubling to 10 s), stops on 4401, 4404 and 1008 (`onStop` gets the reason), and forwards each envelope over a Tauri channel. The returned function calls `events_unsubscribe`, which closes the socket with 1000. The token and the daemon URL never reach the webview.
