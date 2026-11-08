"""Development-only tools, never part of a packaged build.

``SPOOLHQ_DEV_FAKE_RUNNER=<scenario>`` makes ``spool serve`` use the fake runner for
every role with one of ``SCENARIOS`` (``fake_runner.py``), so a run can be watched in
the app without a model. ``spool serve`` refuses it in a frozen (packaged) build.
"""

from spoolhq.devtools.fake_runner import SCENARIOS, dev_agents

__all__ = ["SCENARIOS", "dev_agents"]
