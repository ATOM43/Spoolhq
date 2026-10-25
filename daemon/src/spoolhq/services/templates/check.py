"""The contract check: generate a template into a temp folder and run its gates.

No agent is involved: a template passes when the project it generates installs, lints
and tests clean with the commands its ``spoolhq-template.yaml`` declares.
"""

import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from spoolhq.services.gates import DEFAULT_TIMEOUTS, GateRun, run_gates
from spoolhq.services.git import GitError, remove_path
from spoolhq.services.templates.contract import TemplateContract, TemplateError, load_contract
from spoolhq.services.templates.generate import check_safe, init_repo, render
from spoolhq.services.templates.sources import ResolvedTemplate, open_template


@dataclass(frozen=True)
class CheckResult:
    contract: TemplateContract
    run: GateRun


def check_template(
    source: str,
    *,
    log_dir: Path,
    ref: str | None = None,
    on_resolved: Callable[[ResolvedTemplate], None] | None = None,
) -> CheckResult:
    """Generate ``source`` into a temp folder, ``git init`` it and run install, lint and
    test there (logs in ``log_dir``). The folder is removed afterwards."""
    with open_template(source, ref) as template:
        if on_resolved is not None:
            on_resolved(template)
        contract = load_contract(template.root, template.label)
        check_safe(template.root, template.label)
        work = Path(tempfile.mkdtemp(prefix="spoolhq-template-check-"))
        try:
            project = work / contract.name
            render(template, project, contract.name)
            try:
                init_repo(project, "main", None)
            except GitError as exc:
                raise TemplateError(f"template {template.label!r}: git init failed: {exc}") from exc
            timeouts: dict[str, float] = {
                name: float(seconds) for name, seconds in DEFAULT_TIMEOUTS.items()
            }
            run = run_gates(project, contract.commands.gates(), timeouts, log_dir)
        finally:
            remove_path(work)
    return CheckResult(contract=contract, run=run)
