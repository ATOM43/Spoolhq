"""services/templates/check.py: generate a template into a temp folder and run its gates."""

from pathlib import Path

import pytest

from spoolhq.services.gates import GateStatus
from spoolhq.services.templates import TemplateError, check_template
from tests.conftest import fake_tool_cmd, fixture_contract, make_template

pytestmark = pytest.mark.integration  # the gates start subprocesses


def test_a_passing_template(tmp_path: Path) -> None:
    template = make_template(tmp_path / "tpl")
    seen = []
    result = check_template(str(template), log_dir=tmp_path / "logs", on_resolved=seen.append)
    assert result.run.passed
    assert [r.name for r in result.run.results] == ["install", "lint", "test"]
    assert result.contract.name == "fixture"
    assert [t.label for t in seen] == ["tpl"]
    assert (tmp_path / "logs" / "test.log").is_file()


def test_the_gates_run_in_a_git_work_tree(tmp_path: Path) -> None:
    # git exits 128 outside a work tree; the temp folder is not inside one.
    contract = fixture_contract(lint="git rev-parse --is-inside-work-tree")
    template = make_template(tmp_path / "tpl", contract=contract)
    result = check_template(str(template), log_dir=tmp_path / "logs")
    assert result.run.passed, result.run.results[1].excerpt


def test_a_failing_gate(tmp_path: Path) -> None:
    contract = fixture_contract(test=fake_tool_cmd("fail-test"))
    template = make_template(tmp_path / "tpl", contract=contract)
    result = check_template(str(template), log_dir=tmp_path / "logs")
    assert not result.run.passed
    assert result.run.results[2].status is GateStatus.FAILED


def test_an_invalid_contract_runs_nothing(tmp_path: Path) -> None:
    template = make_template(tmp_path / "x", contract=fixture_contract(install=None))
    with pytest.raises(TemplateError, match="has no 'install' command"):
        check_template(str(template), log_dir=tmp_path / "logs")
    assert not (tmp_path / "logs").exists()
