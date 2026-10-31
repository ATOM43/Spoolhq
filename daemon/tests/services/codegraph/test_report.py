"""The part of Graphify's report that goes into a prompt."""

from spoolhq.services.codegraph import summary
from tests.conftest import GRAPH_REPORT


def test_keeps_the_map_and_drops_the_rest() -> None:
    text = summary(GRAPH_REPORT.read_text(encoding="utf-8"))
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    assert headings == [
        "## Summary",
        "## God Nodes (most connected - your core abstractions)",
        "## Surprising Connections (you probably didn't know these)",
        "## Import Cycles",
        "## Communities (5 total, 1 thin omitted)",
    ]
    assert "### Community 3" in text
    for left_out in ("tmp-0123", "01dd791c", "graphify update", "graphify query", "Suggested"):
        assert left_out not in text
    assert text.endswith("(+4 more)\n")


def test_a_report_without_known_sections_is_empty() -> None:
    assert summary("# Graph Report\r\n\r\nnothing\r\n") == ""
