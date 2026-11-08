"""An attempt's stored gates, review and diff as typed reports."""

import dataclasses
import shlex
import sys
from pathlib import Path

from spoolhq.services.gates import GateResult, GateRun, GateStatus
from spoolhq.services.gates.runner import run_gates
from spoolhq.services.runloop import diff_report, gates_report, review_report
from spoolhq.services.runloop.artifacts import PATCH_LINES


def _stored(run: GateRun) -> dict[str, object]:
    # As machine.run_gates writes gates.json.
    return {"passed": run.passed, "results": [dataclasses.asdict(r) for r in run.results]}


def _result(status: GateStatus, excerpt: str = "", **extra: object) -> GateResult:
    fields = {"output_lines": 0, "output_truncated": False, "log_path": None, **extra}
    return GateResult("test", "just test", status, 1, 2.5, excerpt, (), **fields)  # type: ignore[arg-type]


def test_a_failed_gate_points_at_its_first_failure_line() -> None:
    output = "collected 2 items\n\nt.py .F\nFAILED t.py::test_b - assert 1 == 2\n1 failed"
    report = gates_report(_stored(GateRun((_result(GateStatus.FAILED, output),))))
    (row,) = report.results
    assert (row.state, row.duration_ms, row.first_failure_line) == ("failed", 2500, 3)
    assert output.split("\n")[3].startswith("FAILED")
    assert row.truncated is False


def test_timed_out_error_and_skipped_states() -> None:
    run = GateRun(
        (
            _result(GateStatus.TIMED_OUT, "running…", output_truncated=True),
            _result(GateStatus.ERROR, "gate 'test': program 'just' not found on PATH"),
            _result(GateStatus.SKIPPED),
            _result(GateStatus.PASSED, excerpt_trimmed=True),
        )
    )
    rows = gates_report(_stored(run)).results
    assert [r.state for r in rows] == ["timed_out", "failed", "skipped", "passed"]
    assert [r.first_failure_line for r in rows] == [None, None, None, None]
    assert [r.truncated for r in rows] == [True, False, False, True]


def test_a_real_gate_run_reports_trimmed_output_and_progress(tmp_path: Path) -> None:
    script = tmp_path / "noisy.py"
    script.write_text(
        "for i in range(3000):\n    print('line', i)\n"
        "print('FAILED t.py::x')\nraise SystemExit(1)\n",
        encoding="utf-8",
    )
    started: list[tuple[str, int]] = []
    run = run_gates(
        tmp_path,
        {
            "install": None,
            "lint": None,
            "test": shlex.join([Path(sys.executable).as_posix(), "noisy.py"]),
        },
        {"install": 10, "lint": 10, "test": 30},
        tmp_path / "logs",
        on_gate=lambda name, done: started.append((name, len(done))),
    )
    assert started == [("test", 2)]  # install and lint skipped, before the test starts
    row = gates_report(_stored(run)).results[2]
    assert (row.state, row.truncated) == ("failed", True)
    assert row.first_failure_line is not None
    assert row.output.split("\n")[row.first_failure_line] == "FAILED t.py::x"


def test_stopped_attempts() -> None:
    assert gates_report({"stopped": "max_turns"}).stopped == "max_turns"
    review = review_report({"stopped": "timed_out"})
    assert (review.verdict, review.items, review.stopped) == (None, [], "timed_out")
    unfinished = review_report({"run_outcome": "error", "verdict": None, "items": []})
    assert (unfinished.verdict, unfinished.stopped) == (None, "error")


def test_review_items_in_done_when_order() -> None:
    report = review_report(
        {
            "verdict": "changes_requested",
            "summary": "One item is missing.",
            "items": [
                {"index": 2, "item": "Rollback works", "met": False, "reason": "no down step"},
                {"index": 1, "item": "Migrations run", "met": True, "reason": "ok"},
            ],
        }
    )
    assert report.verdict == "changes_requested"
    assert [(i.text, i.met, i.reason) for i in report.items] == [
        ("Migrations run", True, "ok"),
        ("Rollback works", False, "no down step"),
    ]


DIFF = """\
diff --git a/old name.py b/new name.py
similarity index 90%
rename from old name.py
rename to new name.py
index 1111111..2222222 100644
--- a/old name.py\t
+++ b/new name.py\t
@@ -1,2 +1,2 @@
 keep
-old
+new
diff --git a/gone.txt b/gone.txt
deleted file mode 100644
index 3333333..0000000
--- a/gone.txt
+++ /dev/null
@@ -1,2 +0,0 @@
-a
-b
diff --git a/logo.png b/logo.png
new file mode 100644
index 0000000..4444444
Binary files /dev/null and b/logo.png differ
diff --git "a/caf\\303\\251.md" "b/caf\\303\\251.md"
new file mode 100644
index 0000000..5555555
--- /dev/null
+++ "b/caf\\303\\251.md"
@@ -0,0 +1 @@
+++ a line that starts with two plus signs
diff --git a/run.sh b/run.sh
old mode 100644
new mode 100755
"""


def test_a_diff_with_a_rename_a_deletion_and_a_binary_file() -> None:
    report = diff_report(DIFF)
    rows = [
        (f.path, f.old_path, f.status, f.additions, f.deletions, f.binary) for f in report.files
    ]
    assert rows == [
        ("new name.py", "old name.py", "renamed", 1, 1, False),
        ("gone.txt", None, "deleted", 0, 2, False),
        ("logo.png", None, "added", 0, 0, True),
        ("café.md", None, "added", 1, 0, False),
        ("run.sh", None, "modified", 0, 0, False),
    ]
    assert report.files[0].patch == "@@ -1,2 +1,2 @@\n keep\n-old\n+new"
    assert report.files[2].patch == ""
    assert report.truncated is False


def test_a_3000_line_patch_is_cut() -> None:
    body = "".join(f"+line {i}\n" for i in range(3000))
    text = f"diff --git a/big.py b/big.py\n--- /dev/null\n+++ b/big.py\n@@ -0,0 +1,3000 @@\n{body}"
    report = diff_report(text)
    (file,) = report.files
    assert (file.additions, file.truncated, report.truncated) == (3000, True, True)
    assert len(file.patch.split("\n")) == PATCH_LINES


def test_an_empty_diff_has_no_files() -> None:
    assert diff_report("").files == []
