"""The hello ticket with and without the code map, with the real ``claude`` and the real
Graphify (opt-in: ``SPOOLHQ_REAL_AGENT=1``, a logged-in ``claude``, ``graphify`` on PATH).

Project ``mapped`` runs the ticket twice (T01, then the same ticket as T02): a full build,
then an update against the project's cache. Project ``plain`` runs it with
``context.code_map_chars: 0``. Prints build times, model calls and weighted tokens
(run with ``-s`` to see them).
"""

import logging
import re
import shutil
from pathlib import Path

import pytest

from spoolhq.services.codegraph import tool
from spoolhq.services.codegraph.tool import find_command as real_find_command
from spoolhq.services.projects import init_project, load_project, save_project
from spoolhq.services.runloop import RunLoop
from spoolhq.services.runs import RunRegistry, RunStatus, attempt_dir
from tests.conftest import run_git
from tests.services.agents.test_real_run import REAL, logged_in
from tests.services.runloop.conftest import Merging
from tests.services.runloop.test_real_run import PYTHON, TEST_COMMAND, TICKET, model_calls

pytestmark = [
    pytest.mark.real_agent,
    pytest.mark.integration,
    pytest.mark.skipif(
        not (REAL and logged_in() and shutil.which("graphify")),
        reason="needs SPOOLHQ_REAL_AGENT=1, a logged-in claude and graphify on PATH",
    ),
]

# A little existing code, so the map has something to show.
CODE = {
    "shop/__init__.py": "",
    "shop/prices.py": (
        "def net(gross: float, rate: float) -> float:\n    return gross / (1 + rate)\n"
    ),
    "shop/cart.py": (
        "from shop.prices import net\n\n\nclass Cart:\n    def __init__(self) -> None:\n"
        "        self.items: list[float] = []\n\n    def add(self, price: float) -> None:\n"
        "        self.items.append(price)\n\n    def total_net(self, rate: float) -> float:\n"
        "        return sum(net(p, rate) for p in self.items)\n"
    ),
    "shop/checkout.py": (
        "from shop.cart import Cart\n\n\ndef checkout(cart: Cart) -> str:\n"
        "    return f'{cart.total_net(0.2):.2f}'\n"
    ),
}


def setup(name: str, repo: Path, projects_dir: Path, map_chars: int, tickets: int) -> Path:
    workspace = init_project(name, repo, projects_dir=projects_dir).path
    (workspace / "tickets").mkdir(exist_ok=True)
    for number in range(1, tickets + 1):
        text = TICKET.replace("id: T01", f"id: T{number:02d}")
        (workspace / "tickets" / f"T{number:02d}-say-hello.md").write_text(text, encoding="utf-8")
    settings = load_project(name, projects_dir=projects_dir)
    settings.commands.install = f"{PYTHON} --version"
    settings.commands.lint = f"{PYTHON} -m compileall -q ."
    settings.commands.test = TEST_COMMAND
    settings.context.code_map_chars = map_chars
    for role in ("planner", "implementer", "reviewer"):
        setattr(settings.agents, role, "claude-code-cli")
    save_project(settings, projects_dir=projects_dir)
    return workspace


def run_ticket(
    loop: RunLoop, registry: RunRegistry, name: str, workspace: Path, ticket: str
) -> str:
    run = loop.start(name, "next", ticket)
    loop.wait(name)
    log = registry.get(name).run_log
    final = log.get_run(run.id)
    attempts = log.list_attempts(run.id)
    usage = log.run_usage(run.id)
    calls = sum(model_calls(attempt_dir(workspace, a)) for a in attempts)
    assert final.status is RunStatus.DONE, final.reason
    return (
        f"{name} {ticket}: {len(attempts)} attempt(s), {calls} model calls, "
        f"{usage.weighted_tokens:,} weighted tokens"
    )


def test_hello_with_and_without_the_code_map(
    repo: Path,
    projects_dir: Path,
    tmp_path: Path,
    home: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(tool, "find_command", real_find_command)
    for path, text in CODE.items():
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(text, encoding="utf-8")
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "--quiet", "-m", "shop")
    mapped = setup("mapped", repo, projects_dir, 8_000, tickets=2)
    plain = setup("plain", repo, projects_dir, 0, tickets=1)
    registry = RunRegistry.start(projects_dir, daemon_instance="real")
    loop = RunLoop(
        registry,
        projects_dir=projects_dir,
        worktrees_dir=tmp_path / "worktrees",
        home=home,
        integrator=Merging(),
    )
    lines = []
    try:
        with caplog.at_level(logging.INFO, logger="spoolhq.services.codegraph"):
            lines.append(run_ticket(loop, registry, "mapped", mapped, "T01"))
            lines.append(run_ticket(loop, registry, "mapped", mapped, "T02"))
            lines.append(run_ticket(loop, registry, "plain", plain, "T01"))
    finally:
        loop.close()
        registry.close()

    builds = [r.getMessage() for r in caplog.records if r.getMessage().startswith("code map:")]
    print("\n".join([*builds, *lines]))
    kinds = [match[1] for b in builds if (match := re.match(r"code map: (\w+)", b))]
    assert kinds[:2] == ["full", "update"]
    assert not (repo / "graphify-out").exists()
