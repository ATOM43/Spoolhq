# Ticket file format

A project's plan is a folder of markdown files, one per ticket, in its workspace: `~/spoolhq-projects/<name>/tickets/` (see [Projects](architecture.md#projects)). Each file has YAML frontmatter that SpoolHQ reads and updates, and a free-form body that it reads but never rewrites.

The [planner](planner.md) writes them as `draft` tickets from the spec (`spool plan generate`), with a `## Purpose`, `## Scope` and `## Done when` body; you can also write them by hand. Drafts never run: `spool plan approve` moves them all to `ready`. A draft you edit is kept as it is when you re-plan.

## Example

File `tickets/T04-project-workspace.md`:

```markdown
---
id: T04
title: Project workspace and settings
phase: 1
depends_on: [T02]
status: ready
estimate_h: 2
review_required: false
tracker_ref: null
---

## Scope
- Create the workspace folder and `project.yaml`.

## Done when
- [ ] `spool init` creates the workspace
- [x] Errors name the field
```

## File names

`<id>-<slug>.md`, for example `T04-project-workspace.md`. The part before the first `-` must equal the `id` in the frontmatter. Only `*.md` files are read; hidden files (starting with `.`) and folders are ignored.

## Fields

Unknown keys are errors, so a typo never silently falls back to a default. Values are not converted: `phase: "1"` is a string and fails, and `review_required: yes` is the string `yes` (YAML 1.2), not `true`.

| Key | Required | Default | Rules |
| --- | --- | --- | --- |
| `id` | yes | | `T` followed by 2 or 3 digits (`T04`, `T104`). Must match the file-name prefix. |
| `title` | yes | | Non-empty string. |
| `phase` | yes | | Whole number, 0 or more. |
| `depends_on` | no | `[]` | List of ticket ids. No duplicates, and a ticket cannot depend on itself. |
| `status` | yes | | One of `draft`, `ready`, `running`, `awaiting_approval`, `blocked`, `done`. The planner writes `draft`. |
| `estimate_h` | yes | | Hours: a number above 0 and at most 40. |
| `review_required` | no | `false` | `true` or `false`. |
| `tracker_ref` | no | `null` | The ticket's id in an external tracker, or `null`. |

Only single files are checked here. Whether every `depends_on` id exists, whether the dependencies form a cycle, and which status changes are allowed are checks on the whole plan: see [scheduler.md](scheduler.md).

## Body

Everything after the closing `---` is the body: any markdown you like (scope, notes, links, code). SpoolHQ keeps it as the exact original text.

### Done when

The checklist under the `## Done when` heading is read for later steps (the reviewer, the UI) as a list of items with their text and whether they are checked:

- Items are `- [ ] text` or `- [x] text` (`*` and `+` bullets and a capital `X` work too); nested items count.
- The heading may be any level and any case (`### Done When`); the section ends at the next heading of the same or a higher level, so sub-headings stay inside it.
- Headings and items inside fenced code blocks are ignored.
- A missing section, or one with no checklist items, is a warning, not an error.

## Errors

Every problem is reported at once, one line each, as `tickets/<file>: <field>: <message>`:

| Problem | Message |
| --- | --- |
| Bad id | `tickets/T4-x.md: id: must be T followed by 2 or 3 digits, like T04` |
| Id differs from the file name | `tickets/T04-x.md: id: 'T05' does not match the file name prefix 'T04'` |
| Bad file name | `tickets/notes.md: file name must be <id>-<slug>.md, like T04-project-workspace.md` |
| Missing field | `tickets/T04-x.md: title: field required` |
| Unknown key | `tickets/T04-x.md: stauts: unknown key (did you mean 'status'?)` |
| Unknown status | `tickets/T04-x.md: status: must be one of draft, ready, running, awaiting_approval, blocked, done` |
| Self-dependency | `tickets/T04-x.md: depends_on: T04 cannot depend on itself` |
| Duplicate dependency | `tickets/T04-x.md: depends_on: T02 is listed more than once` |
| Dependency not an id | `tickets/T04-x.md: depends_on: 't2' is not a ticket id (must be T followed by 2 or 3 digits, like T04)` |
| Estimate out of range | `tickets/T04-x.md: estimate_h: must be greater than 0` (or `must be at most 40`) |
| Wrong type | `tickets/T04-x.md: phase: input should be a valid integer` |
| No frontmatter | `tickets/T04-x.md: line 1: the file must start with a '---' line opening the frontmatter` |
| Frontmatter not closed | `tickets/T04-x.md: the frontmatter is not closed: add a '---' line after it` |
| YAML syntax error | `tickets/T04-x.md: line 4, column 6: expected ',' or ']', but got ':'` |
| Not UTF-8 | `tickets/T04-x.md: not UTF-8 text (invalid byte at offset 22)` |

YAML line numbers count from the top of the file, so line 1 is the opening `---`.

## Round-trip guarantee

Reading a ticket and saving it unchanged writes the same bytes. When SpoolHQ changes a ticket (for example its `status`):

- Only the lines of the frontmatter keys whose value changed are rewritten. Every other line keeps its comments, order, quoting and spacing; a changed value keeps the quote style it had, a block or flow list keeps its layout, and a comment at the end of the key's line stays. Comments inside a changed multi-line value (between list items) are not kept.
- A key that was not in the file is added at the end of the frontmatter.
- The body is written back exactly as it was read.
- Line endings (LF or CRLF), a missing or present final newline, a UTF-8 byte-order mark and all non-ASCII text are kept.
- Saves are atomic (temp file and rename), so a crash never leaves a half-written file.

If a frontmatter cannot be updated line by line (it is written as one `{...}` flow mapping, say), SpoolHQ re-renders the whole frontmatter with ruamel.yaml instead; comments are kept, but spacing may change.

## Commands

| Command | What it does |
| --- | --- |
| `spool tickets list <project> [--status S] [--phase N]` | Table of id, status, phase, title, dependencies and estimate, sorted by id. Invalid files are listed at the end with their errors, and the command then exits 1. |
| `spool tickets show <project> <id>` | The frontmatter fields, the Done-when checklist and the body. Warnings go to stderr. |
| `spool tickets edit <project> <id>` | Opens the file in your editor, then checks it. |
| `spool tickets set-status <project> <id> <status>` | Changes the status if the [transition table](scheduler.md#status-transitions) allows it; only the `status` line changes. |

These read the files directly; the daemon does not need to be running.

## Editing

`spool tickets edit` opens the ticket in `$VISUAL`, or `$EDITOR` if `VISUAL` is not set, or `nano` (`notepad` on Windows) if neither is. The setting may include arguments, such as `code --wait`. It is split like a shell would split words (`shlex`; on Windows backslashes in paths are kept) and run as an argument list, never through a shell, so `;`, `&&` or `$VAR` in it have no special meaning.

Before the editor opens, the file is copied to a hidden backup, `tickets/.<file>.bak`. When the editor exits, the file is checked again:

- **Valid**: the backup is deleted and any warnings are shown.
- **Invalid**: the errors are printed and you are asked whether to reopen the editor. Answer `n` (or press Ctrl-C) to restore the previous version from the backup.

An invalid ticket can be opened with `edit` too, to fix it.
