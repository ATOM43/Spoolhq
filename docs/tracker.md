# Tracker sync

SpoolHQ can mirror a project's tickets to an issue tracker, one way: the ticket files stay the source of truth and the tracker shows them. ClickUp is the first tracker. The code is in `daemon/src/spoolhq/services/tracker/`.

## What gets synced

- **Each ticket** becomes a task named `T04 · <title>`. Its description is the ticket's body (scope and "Done when", as markdown) plus the line "Synced by SpoolHQ · edit in SpoolHQ, not here". Its status is the ticket's status mapped through `tracker.status_map`.
- **Each finished run** adds a comment to its ticket's task when `tracker.comment_on_runs` is on (the default): the outcome, the number of attempts, the usage (tokens, plus USD when the backend reported a cost) and the pull request or the commit. The comment is built by code from the run log, never from ticket text or agent output.
- **Each pull request** adds the comment "Pull request: <url>", once.

What the sync doesn't do:

- **Edits made in the tracker are overwritten** by the next push of that ticket. Change the ticket in SpoolHQ.
- **Deleting a ticket leaves its task alone.** Delete the task in the tracker yourself if you want it gone.
- **Renaming a task in the tracker breaks the crash recovery** below: SpoolHQ finds a task by its `T04 · ` prefix only when the ticket's `tracker_ref` is missing. The next push renames the task back.
- Runs that ended before sync first started get no comment.

## ClickUp setup

1. Create a personal API token in ClickUp (Settings › Apps; it starts with `pk_`).
2. Store it: in the app's Settings › Accounts › ClickUp token (the Test button checks it with one read-only call), or set `SPOOLHQ_CLICKUP_TOKEN` in the daemon's environment, which wins over the keychain. The token is only ever sent in the `Authorization` header to `api.clickup.com`; it never appears in logs, events, errors or files.
3. Find the list's id: open the list in ClickUp; it is the number after `/li/` in the address (or use **Copy link**).
4. Add a `tracker` block to `project.yaml` (or pass `--clickup-list` to `spool init`):

   ```yaml
   tracker:
     kind: clickup
     list_id: "901234567"
   ```

5. Nothing else: the daemon starts its sync thread when a project's settings are saved with a `tracker` block (through the app or `PUT …/settings`), and for a block added to the file by hand at the next look at the project's sync state (the app does that within 15 s; so do `spool tracker status` and `spool tracker push`). It then keeps the list up to date by itself.

`spool tracker push <project> --dry-run` prints what a push would do (create, update with the status it sets, comment), from the files and the run log alone: it needs no daemon, writes nothing and sends no request. Since it doesn't ask ClickUp, a task the crash recovery would adopt shows as a create.

`spool tracker status <project>` (or `GET /api/projects/{project}/tracker`) shows the state:

| State | Meaning |
| --- | --- |
| `off` | No `tracker` block. Nothing is queued and the sync thread doesn't start for it. |
| `ok` | Nothing waiting. |
| `syncing` | Actions are waiting to be sent. |
| `failed` | An action failed 5 times (`last_error` says why, `failed_at` when). Later actions still try; the first success, or a retry, clears it. |

## In the app

Only for a project with a `tracker` block, the project header shows a sync line next to the remote, as icon + label:

| Line | Means |
| --- | --- |
| ClickUp · synced 2 min ago | `ok`; the absolute time on hover ("up to date" before the first send) |
| ClickUp · syncing · 3 pending | `syncing` |
| ClickUp · sync failed (red) | `failed`; the error in the tooltip (as plain text), and **Retry** |

**Push now** beside it queues every ticket again (`POST …/tracker/push`); it is disabled, with the reason on hover, while a sync is going.

A failed sync is also a **Needs you** card on Home: "ClickUp sync failed", the project, the error, how long ago it failed, and **Retry**. It goes away once the sync is `ok` again.

Sync runs outside ticket runs, so the run event stream doesn't carry it: the app asks `GET …/tracker` every 15 s, only for projects with a tracker that are on screen (Home, or that project's panel), and right after Push now or Retry.

## Status map

`tracker.status_map` maps each ticket status to a status of the list. The defaults use a new ClickUp list's three statuses, so a fresh list works without it:

```yaml
tracker:
  kind: clickup
  list_id: "901234567"
  status_map:            # SpoolHQ status → tracker status
    draft: to do
    ready: to do
    running: in progress
    awaiting_approval: in progress
    blocked: in progress
    done: complete
  comment_on_runs: true
```

Set only the statuses you want to change; the others keep their defaults. Names compare case-insensitively, and SpoolHQ sends the list's own spelling. Before its first write the ClickUp adapter reads the list's statuses; one the list doesn't have fails sync with "ClickUp list has no status '<x>'; set tracker.status_map.<status>".

## The outbox and failures

Nothing in the run loop calls the tracker, so a slow or broken tracker never delays a run or changes its outcome.

Every 5 seconds the daemon's sync thread looks at each project with a `tracker` block and queues what changed since its last look in the outbox, a table in the project's `state.db` (schema 9):

- a **push** when a ticket is new or its title or body changed;
- a **status** update when only its status changed;
- a **comment** for each finished run and each pull request, keyed by the run id, so each is queued once, across restarts too.

It then sends the due actions one at a time, oldest first. Repeated changes coalesce: a ticket has at most one push and one status update waiting, a waiting push covers a status change, and every action sends the ticket as it is when it goes out, so three quick status changes end in one update with the latest status.

| What happens | What SpoolHQ does |
| --- | --- |
| An error or a timeout (10 s) | Retries after 5 s, doubling up to 10 minutes. |
| The 5th failure of one action | Marks it failed, sets the project's state to `failed` with the message, records a `tracker.failed` event on the ticket's latest run (`{"action", "ticket_id", "error"}`) and logs it. |
| A rate limit (HTTP 429) | Sends nothing for that project until the time in `X-RateLimit-Reset` (60 s when missing). Not counted as a failure. |
| No token | A failure with "No clickup token; set it in Settings or SPOOLHQ_CLICKUP_TOKEN". |
| The ticket was deleted | The action is dropped. |

A failed action stays failed until **Retry** in the app (or `POST …/tracker/retry`) puts every failed action back in the queue with its failures reset and clears the `failed` state; with nothing failed it does nothing. `spool tracker push` queues every ticket again.

`last_error` is always one of the fixed messages above, built by SpoolHQ ("ClickUp answered 500", "ClickUp timed out", …): never a response body, a header or the token.

### Idempotency and crash recovery

A push updates the task in the ticket's `tracker_ref` when there is one. Otherwise the adapter looks for a task in the list (closed ones too) whose name starts with `T04 · ` and adopts it; only when there is none does it create a task. The new task's id is then written to the ticket's `tracker_ref` through the ticket store, under the same locks the API and `spool tickets new` take. So pushing the same plan twice creates no duplicates, and a daemon stopped between creating a task and writing its id adopts the task on the next push.

## The interface

`services/tracker/base.py` defines `TrackerAdapter`:

| Method | Does |
| --- | --- |
| `push_ticket(ticket) -> ref` | Update the task in `ticket.meta.tracker_ref`; without one, adopt the task named `task_prefix(ticket.id)…` or create one. Sends the name, `description(ticket)` and the mapped status. Returns the task's ref. |
| `update_status(ref, status)` | Set the task's status to the one the ticket status maps to. |
| `comment(ref, text)` | Add a comment. |
| `link_pr(ref, url)` | Add "Pull request: <url>". |
| `close()` | Release the HTTP client. |

Errors are `TrackerError` with a fixed message, never a token, header or response body; `retry_after` (seconds) marks a rate limit. The sync service (`sync.py`) and the dry run use nothing else.

### Writing an adapter

1. Write a class with the methods above in `services/tracker/<name>.py`. Keep calls to one fixed HTTPS host, without redirects, with a timeout; check any id from a ticket file before putting it in a URL.
2. Add it to `ADAPTERS` in `services/tracker/registry.py` and to `Tracker.kind` in `services/projects/model.py`, so `project.yaml` refuses any other value at `tracker.kind`. Its token is the secret named like the kind (`services/secrets`).
3. Add it to the contract suite in `daemon/tests/services/tracker/test_contract.py` with a fake server on `httpx.MockTransport`: create once then update, adopt by name, map statuses, comment and link. Tests never call a real tracker.

## ClickUp API

Checked against ClickUp's API v2 reference on 2026-11-21:

| Call | Used for |
| --- | --- |
| `GET /api/v2/list/{list_id}` | the list's `statuses` (each `status` name), once per adapter |
| `GET /api/v2/list/{list_id}/task?page=N&include_closed=true` | finding a task by name; 100 per page, `last_page` ends it; read once per adapter |
| `POST /api/v2/list/{list_id}/task` | creating a task: `name`, `markdown_content`, `status`; the answer's `id` |
| `PUT /api/v2/task/{task_id}` | updating `name`, `markdown_content`, `status` |
| `POST /api/v2/task/{task_id}/comment` | `comment_text`, with `notify_all: false` (required) |

The personal token goes in `Authorization` without `Bearer`. The rate limit is per token per minute: 100 on the Free, Unlimited and Business plans, 1,000 on Business Plus, 10,000 on Enterprise. A 429 carries `X-RateLimit-Reset`, a Unix time (read as seconds, or milliseconds when it is that large).
