# templates

The built-in project templates live in the daemon package, at [`daemon/src/spoolhq/templates/`](../daemon/src/spoolhq/templates/), so they ship with `spool` as package data. Each is a Copier template with a `spoolhq-template.yaml` that names the `install`, `lint` and `test` commands SpoolHQ's gates run for projects built from it. See [docs/templates.md](../docs/templates.md).
