"""Integrate T01 of ``demo`` and die (``os._exit(1)``) right after journal state ``argv[1]``.

Run by ``test_integration_crash.py`` as ``python -m tests.services.runloop.crash_child
<state> <projects_dir> <worktrees_dir>``, with the test's ``SPOOLHQ_HOME`` in the
environment. Exits 0 if the state was never reached.
"""

import os
import sys
from pathlib import Path

from spoolhq.core.config import home_dir
from spoolhq.services.agents import FakeRunner
from spoolhq.services.runloop import Agents, LocalIntegrator, RunLoop
from spoolhq.services.runs import RunRegistry
from tests.services.runloop.conftest import FakeGates


def main(state: str, projects_dir: Path, worktrees_dir: Path) -> None:
    def checkpoint(reached: str) -> None:
        if reached == state:
            os._exit(1)

    registry = RunRegistry.start(projects_dir, daemon_instance="child")
    unused = FakeRunner([])
    loop = RunLoop(
        registry,
        projects_dir=projects_dir,
        worktrees_dir=worktrees_dir,
        home=home_dir(),
        agents=Agents(unused, unused),
        integrator=LocalIntegrator(checkpoint=checkpoint),
        gates=FakeGates(),
    )
    loop.integrate_ticket("demo", "T01")
    loop.wait("demo")
    loop.close()
    registry.close()


if __name__ == "__main__":
    main(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]))
