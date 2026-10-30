"""services/git/diffstat.py: the staged squash's files and line counts."""

from pathlib import Path

from spoolhq.services.git import ChangedFile, parse_numstat, staged_changes
from tests.conftest import commit_file, run_git


def test_parse_numstat_with_a_rename_and_a_binary() -> None:
    fields = [
        "3\t1\tsrc/a.py",
        "-\t-\tlogo.png",
        "0\t0\t",
        "src/x.py",
        ".github/x.py",
        "2\t0\tb c.py",
    ]
    out = "".join(f"{field}\0" for field in fields)
    assert parse_numstat(out) == [
        ChangedFile("src/a.py", None, 3, 1),
        ChangedFile("logo.png", None, 0, 0),
        ChangedFile(".github/x.py", "src/x.py", 0, 0),
        ChangedFile("b c.py", None, 2, 0),
    ]
    assert parse_numstat("") == []


def test_staged_changes_names_both_sides_of_a_rename(wt_repo: Path) -> None:
    base = commit_file(wt_repo, "x.py", "".join(f"line {i}\n" for i in range(20)), "x")
    run_git(wt_repo, "mv", "x.py", "moved.py")
    (wt_repo / "new.py").write_text("a\nb\n", encoding="utf-8")
    (wt_repo / "blob.bin").write_bytes(b"\0\1\2")
    run_git(wt_repo, "add", "--all")
    changes = sorted(staged_changes(wt_repo, base), key=lambda c: c.path)
    assert changes == [
        ChangedFile("blob.bin", None, 0, 0),
        ChangedFile("moved.py", "x.py", 0, 0),
        ChangedFile("new.py", None, 2, 0),
    ]
