"""ETag-guarded writes."""

import threading
from pathlib import Path

import pytest

from spoolhq.services.projects import EditConflict, etag_of, read_with_etag, write_if_match


def test_write_only_when_the_etag_matches(tmp_path: Path) -> None:
    path = tmp_path / "CONTEXT.md"
    path.write_bytes(b"one")
    _, first = read_with_etag(path)
    assert first == etag_of(b"one") and first.startswith('"')

    new = write_if_match(tmp_path, path, first, lambda: path.write_bytes(b"two"))
    assert (path.read_bytes(), new) == (b"two", etag_of(b"two"))

    with pytest.raises(EditConflict) as conflict:
        write_if_match(tmp_path, path, first, lambda: path.write_bytes(b"three"))
    assert (conflict.value.etag, conflict.value.data) == (new, b"two")
    assert path.read_bytes() == b"two"


def test_concurrent_edits_with_the_same_etag_let_one_win(tmp_path: Path) -> None:
    path = tmp_path / "CONTEXT.md"
    path.write_bytes(b"base")
    etag = etag_of(b"base")
    outcomes: list[str] = []

    def edit(text: bytes) -> None:
        try:
            write_if_match(tmp_path, path, etag, lambda: path.write_bytes(text))
            outcomes.append("saved")
        except EditConflict:
            outcomes.append("conflict")

    threads = [threading.Thread(target=edit, args=(f"v{i}".encode(),)) for i in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(outcomes) == ["conflict"] * 7 + ["saved"]
