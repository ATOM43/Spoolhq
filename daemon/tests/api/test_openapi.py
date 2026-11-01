"""The committed OpenAPI schema the TypeScript client is generated from must match the
daemon's: run `just gen-api` after changing the API."""

import importlib.util
from pathlib import Path

REPO = Path(__file__).parents[3]
COMMITTED = REPO / "desktop" / "src" / "shared" / "api" / "openapi.json"


def test_committed_schema_matches_the_daemon() -> None:
    spec = importlib.util.spec_from_file_location(
        "dump_openapi", REPO / "scripts" / "dump_openapi.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert COMMITTED.read_text(encoding="utf-8") == module.schema(), (
        "desktop/src/shared/api/openapi.json is stale; run `just gen-api`"
    )


def test_event_models_are_in_the_schema() -> None:
    import json

    schemas = json.loads(COMMITTED.read_text(encoding="utf-8"))["components"]["schemas"]
    assert {"EventEnvelope", "AuthMessage", "RunStatusData", "ErrorResponse"} <= set(schemas)
