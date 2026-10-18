"""Allow `python -m spoolhq`, the same as the `spool` command."""

from spoolhq.cli import app

app(prog_name="spool")
