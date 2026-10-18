# SpoolHQ

SpoolHQ is an open-source, local-first desktop app that turns a written spec into a ticket plan, then has a coding agent implement the tickets one at a time, with tests and review before each merge. A Python daemon runs the loop, a `spool` CLI drives it, and a Tauri desktop app shows what is happening.

**Status: pre-alpha, not usable yet.** The daemon serves a minimal authenticated API; nothing else works yet.

## Development quickstart

Install [uv](https://docs.astral.sh/uv/), [Node.js 24 LTS](https://nodejs.org/), [pnpm](https://pnpm.io/) and [just](https://just.systems/), then:

```sh
just install && just test
```

## Run the daemon

```sh
uv run --directory daemon spool serve     # or: just dev
```

The daemon listens on `http://127.0.0.1:8765` only; the interactive API docs are at `/docs`. On first start it writes a random access token to `~/.spoolhq/token` (readable only by you); the `spool` CLI reads it from there, and every `/api/*` route except `/api/health` needs it as `Authorization: Bearer <token>`. Settings live in `~/.spoolhq/config.toml` (`port`, `log_level`) and can be overridden with `SPOOLHQ_PORT` and `SPOOLHQ_LOG_LEVEL`; set `SPOOLHQ_HOME` to use another folder. Logs are JSON lines in `~/.spoolhq/logs/daemon.log`.

`uv run --directory daemon spool version` prints the CLI's version and, if the daemon is running, the daemon's.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow and [DECISIONS.md](DECISIONS.md) for why things are the way they are.

## Licence

[Apache-2.0](LICENSE)
