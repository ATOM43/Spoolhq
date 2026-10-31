"""Code graph: a map of the repository from Graphify, for the agent's prompt.

``refresh(source, workspace)`` builds or incrementally updates the graph of ``source``
with the project's cache in ``<workspace>/.spoolhq/codegraph/`` and returns the report's
summary; ``probe()`` finds Graphify. Graphify is optional: without it, or when it fails,
callers get None and carry on. This package imports no other service package; callers
pass plain paths in. See ``docs/codegraph.md``.
"""

from spoolhq.services.codegraph.cache import CACHE_DIR, CodeMap, cache_dir, refresh
from spoolhq.services.codegraph.report import summary
from spoolhq.services.codegraph.tool import TESTED_VERSION, Graphify, GraphifyError, probe

__all__ = [
    "CACHE_DIR",
    "TESTED_VERSION",
    "CodeMap",
    "Graphify",
    "GraphifyError",
    "cache_dir",
    "probe",
    "refresh",
    "summary",
]
