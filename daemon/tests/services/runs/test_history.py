"""Paged run history and its cursor."""

from pathlib import Path

import pytest

from spoolhq.services.runs import RunLog, decode_cursor, encode_cursor, page_runs


def test_pages_newest_first_and_cursor_round_trip(tmp_path: Path) -> None:
    with RunLog(tmp_path, daemon_instance="test") as log:
        runs = [log.start_run("T01") for _ in range(5)]
        first = page_runs(log, None, 2)
        assert [run.id for run in first.runs] == [5, 4]
        assert first.next_cursor is not None
        assert decode_cursor(first.next_cursor) == (runs[3].started_at, 4)
        rest = page_runs(log, first.next_cursor, 10)
        assert ([run.id for run in rest.runs], rest.next_cursor) == ([3, 2, 1], None)
        assert decode_cursor(encode_cursor(runs[0])) == (runs[0].started_at, 1)


@pytest.mark.parametrize("cursor", ["!!!", "bm9waXBl", "fGFiYw", "YXxi"])
def test_bad_cursors_are_refused(cursor: str) -> None:
    with pytest.raises(ValueError, match="invalid cursor"):
        decode_cursor(cursor)
