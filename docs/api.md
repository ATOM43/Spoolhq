# Daemon API

The daemon listens on `127.0.0.1` only (port 8765 unless `port` says otherwise). Every `/api/*` route needs the token from `~/.spoolhq/token` as `Authorization: Bearer <token>`, except `GET /api/health`; the event WebSocket takes it in its first message instead ([below](#event-websocket)). A request with a foreign `Host` header gets 400, a body over 1 MB gets 413.

The OpenAPI schema is at `/openapi.json` and `/docs` while the daemon runs. The desktop app's typed client is generated from it (see [TypeScript client](#typescript-client)).

## Endpoints

`{name}` is a project name (lowercase letters, digits and hyphens); `{id}` a ticket id, `T` and two or three digits. Both are checked by pattern before any route code runs (422 otherwise), so neither can become a path.

| Route | Does |
| --- | --- |
| `GET /api/health` | `{"status": "ok"}`, no token |
| `GET /api/version` | the daemon's version |
| `GET /api/projects` | each project: `name`, `done`/`total` tickets, `run_state` (`running`, `paused` or `idle`), `needs_you` (tickets `awaiting_approval` or `blocked`), `latest_seq` (see [Starting from REST](#event-websocket)) |
| `POST /api/projects` | create a project like `spool init`: `{"name", "repo", "branch", "remote", "template", "template_ref"}` (201) |
| `POST /api/projects/{name}/commands/test` | `{"gate", "command"}`: run one stack command once in the project's repository, [as its gate would](#trying-a-stack-command) |
| `GET /api/projects/{name}` | the summary plus `repo`, `default_branch`, `remote`, `invalid_tickets`, and what can run: `next_ticket` (what `run/next` would start, else null), `idle` (`{code, ticket_ids, message}` when nothing can: `all_done`, `running`, `awaiting_approval`, `blocked`, `waiting`, `plan_not_approved` or `invalid_plan`; null with no tickets) and `remaining_h` |
| `GET`, `PUT /api/projects/{name}/settings` | `project.yaml` as `{"settings": {...}}`, validated by the project model; [ETag](#etags-and-edit-conflicts) |
| `GET`, `PUT /api/projects/{name}/spec` | `CONTEXT.md` as `{"content": "..."}`; ETag |
| `GET /api/projects/{name}/tickets?status=&phase=` | `{"tickets": [...], "invalid": [...]}`; each ticket is `id`, `file_name`, `meta` (the frontmatter), `body` |
| `GET`, `PUT /api/projects/{name}/tickets/{id}` | one ticket; PUT takes `{"meta", "body"}`; ETag |
| `POST /api/projects/{name}/tickets/{id}/unblock` | `{"note"}`: continue a blocked ticket's run with the note (409 `not_blocked`) |
| `POST /api/projects/{name}/tickets/{id}/approve` (`/integrate`), `/reject`, `/discard` | see [run-loop.md](run-loop.md#api-and-cli) |
| `POST /api/projects/{name}/plan/generate`, `/plan/approve` | see [planner.md](planner.md#api) |
| `POST /api/projects/{name}/run/next`, `/run/all`, `/run/ticket/{id}` | start a run (201) |
| `POST /api/projects/{name}/run/pause`, `/run/resume`, `/run/cancel` | the current run (or `?run_id=`) |
| `GET /api/projects/{name}/runs/current` | the active (else latest) run with its phase lines, tokens and `cost_micro_usd` (null unless an API-key backend reported a cost), and `latest_seq` |
| `GET /api/projects/{name}/runs?cursor=&limit=` | the run history, [paged](#paged-run-history) |
| `GET /api/projects/{name}/runs/{run_id}` | one run with its `attempts` (number, kind, status — the verdict —, backend, tokens, times) |
| `GET /api/projects/{name}/runs/{run_id}/attempts/{n}/{artifact}` | an attempt's file as stored; `artifact` is `transcript`, `gates`, `diff` or `review` (422 for anything else) |
| `POST /api/projects/{name}/github/sync` | check open pull requests now |
| `GET /api/templates` | the built-in templates: `name` (what `POST /api/projects` takes as `template`) and `description` |
| `GET /api/agents` | what `spool agents` shows: each backend (installed, version, login, policy parts) and Graphify |
| `GET /api/settings` | the daemon's settings, and for each secret (`anthropic`, `github`, `clickup`) only `{"set", "source": "keychain" \| "env" \| null}` |
| `PUT`, `DELETE /api/settings/secrets/{name}` | store `{"value"}` in the OS keychain, or remove it (204) |
| `WS /api/projects/{name}/events?since=` | [live events](#event-websocket) |

An artifact is read from the attempt folder the run log names, by a fixed file name per `artifact`; the folder must resolve inside the workspace's `runs/`, and the file must not be a symlink and must resolve inside the folder, else 404.

A secret's value is write-only: it goes to the OS keychain (service `spoolhq`, through `keyring`) and is never returned, logged or written to a file. An environment variable (`ANTHROPIC_API_KEY`, `SPOOLHQ_GITHUB_TOKEN`, `SPOOLHQ_CLICKUP_TOKEN`) wins over the keychain, as it does where the secret is used. Without a usable keychain the answer is 409 `keychain_unavailable`.

## Trying a stack command

The New project dialog's **Test** button. The command is split with the gates' rules (`shlex`, no shell syntax: `&&`, `|`, `;`, redirects and `$(` are 422 with `field: "command"`), its program is looked up on the gates' scrubbed `PATH`, and it runs in the project's `repo` with the gates' environment (no secrets), stdin closed and a 90 s timeout that stops the whole process tree. It can change the checkout, as the gate would. The answer is `{"status": "passed" | "failed" | "timed_out" | "error", "exit_code", "duration_s", "output", "output_truncated", "timeout_s"}`; `output` is the trimmed excerpt the gates show (for `error`, why the program couldn't start). The 90 s stays below the desktop app's 120 s request timeout; a run still uses the project's own `gates.timeouts`.

## Errors

Every non-2xx answer has one shape:

```json
{"error": {"code": "edit_conflict", "message": "the file changed since you loaded it; reload and edit again", "field": null}}
```

`code` is snake_case and stable; `message` is for people; `field` names the offending input when there is one (`limit`, `cursor`, `meta.title`). Messages never repeat request values. Codes in use: `bad_request`, `bad_host`, `unauthorized`, `not_found`, `method_not_allowed`, `validation_error` (422), `conflict` (409, a refusal with the reason), `run_locked`, `not_blocked`, `invalid_transition`, `template_error`, `keychain_unavailable`, `precondition_required` (428), `edit_conflict` (412), `payload_too_large` (413), `limit_too_large` and `invalid_cursor` (400).

## ETags and edit conflicts

Tickets, the spec and `project.yaml` carry an `ETag`: the quoted SHA-256 of the file's bytes, on every GET and after every successful PUT.

1. GET the file; keep its `ETag`.
2. PUT the edit with `If-Match: <that ETag>`. Without `If-Match` the answer is 428 `precondition_required`.
3. If the file changed in between (another client, `spool tickets edit`, an editor), the answer is 412 `edit_conflict` with the current `etag` and `current` content (as the GET returns it) inside `error`, and the file is left as it is. Show the user both, then PUT again with the new ETag.

The daemon reads the bytes, hashes and compares them, and writes (a temp file in the same folder, then `os.replace`), all under the project's edit lock, so two API edits never both win. Writers outside the daemon don't take that lock: an editor saving in the moment between the compare and the replace is overwritten. The window is a few milliseconds.

A ticket PUT goes through the ticket store, so only frontmatter keys whose value changed are rewritten and the body is kept byte for byte (an unchanged PUT writes the same bytes); a status change must be allowed by the scheduler's transition table (409 `invalid_transition`), and the id must still match the file name (422).

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
