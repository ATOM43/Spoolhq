"""Reading a coverage total from Cobertura XML or a JSON summary, and main's store."""

from pathlib import Path

import pytest

from spoolhq.services.gates import read_total, store_total, stored_total


@pytest.mark.parametrize(
    ("text", "total"),
    [
        ('<?xml version="1.0" ?>\n<coverage version="7" line-rate="0.912" branch-rate="0">', 91.2),
        ('{"totals": {"percent_covered": 88.4321}}', 88.43),
        ('{"total": {"lines": {"pct": 75}}}', 75.0),
        ('{"totals": {"percent_covered": "high"}}', None),
        ('{"totals": {"percent_covered": 120}}', None),
        ("<report/>", None),
        ("{broken", None),
    ],
)
def test_read_total(tmp_path: Path, text: str, total: float | None) -> None:
    (tmp_path / "coverage.xml").write_text(text, encoding="utf-8")
    assert read_total(tmp_path, "coverage.xml") == total


def test_a_missing_report_or_one_outside_the_worktree_has_no_total(tmp_path: Path) -> None:
    worktree = tmp_path / "wt"
    worktree.mkdir()
    (tmp_path / "out.json").write_text('{"total": {"lines": {"pct": 99}}}', encoding="utf-8")
    assert read_total(worktree, "coverage.xml") is None
    assert read_total(worktree, "../out.json") is None


def test_main_total_round_trips(tmp_path: Path) -> None:
    assert stored_total(tmp_path) is None
    store_total(tmp_path, 91.2, "T07")
    assert stored_total(tmp_path) == 91.2
    (tmp_path / "coverage.json").write_text("nonsense", encoding="utf-8")
    assert stored_total(tmp_path) is None
