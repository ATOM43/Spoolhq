"""Write the daemon's OpenAPI schema (JSON) to the given file, without starting a server.

`just gen-api` writes desktop/src/shared/api/openapi.json; the drift test in
daemon/tests/api/test_openapi.py compares the committed file with `schema()`.
"""

import json
import sys
from pathlib import Path

from spoolhq.api import create_app
from spoolhq.core.config import Settings


def schema() -> str:
    # Fixed settings: the schema must not depend on the machine it is dumped on.
    app = create_app(Settings.model_construct(), token="x")  # noqa: S106 - no server runs
    return json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    Path(sys.argv[1]).write_text(schema(), encoding="utf-8", newline="\n")
