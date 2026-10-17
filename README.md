# SpoolHQ

SpoolHQ is an open-source, local-first desktop app that turns a written spec into a ticket plan, then has a coding agent implement the tickets one at a time, with tests and review before each merge. A Python daemon runs the loop, a `spool` CLI drives it, and a Tauri desktop app shows what is happening.

**Status: pre-alpha, not usable yet.** The repository holds tooling and placeholders only.

## Development quickstart

Install [uv](https://docs.astral.sh/uv/), [Node.js 24 LTS](https://nodejs.org/), [pnpm](https://pnpm.io/) and [just](https://just.systems/), then:

```sh
just install && just test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow and [DECISIONS.md](DECISIONS.md) for why things are the way they are.

## Licence

[Apache-2.0](LICENSE)
