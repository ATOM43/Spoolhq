"""A stand-in lint/test tool for the gate tests: ``python fake_tool.py <mode> [arg]``.

Modes: pass, fail-test, lint-error, sleep, sleep-with-child <pid file>, flood,
print-env, ansi, marker <file>. Standard library only.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

FAIL_TEST = """\
============================= test session starts ==============================
collected 3 items

tests/test_math.py F.F                                                    [100%]

=================================== FAILURES ===================================
___________________________________ test_add ___________________________________

    def test_add():
>       assert 1 + 1 == 3
E       assert 2 == 3

tests/test_math.py:2: AssertionError
=========================== short test summary info ============================
FAILED tests/test_math.py::test_add - assert 2 == 3
FAILED tests/test_math.py::test_sub - assert 0 == 1
FAILED tests/test_math.py::test_add - assert 2 == 3
========================= 2 failed, 1 passed in 0.01s ==========================
"""


def main() -> int:
    mode = sys.argv[1]
    if mode == "pass":
        print("3 passed")
        return 0
    if mode == "fail-test":
        sys.stdout.write(FAIL_TEST)
        return 1
    if mode == "lint-error":
        print("Checking 4 files")
        print("src/app.py:3:1: error: Name 'x' is not defined  [name-defined]")
        print("Found 1 error in 1 file")
        return 1
    if mode == "sleep":
        print("sleeping", flush=True)
        time.sleep(60)
        return 0
    if mode == "sleep-with-child":
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])  # noqa: S603
        Path(sys.argv[2]).write_text(str(child.pid), encoding="utf-8")
        time.sleep(60)
        return 0
    if mode == "flood":
        # 50,002 lines: a header, 49,998 passing, two failures and the summary.
        lines = ["collected 50000 items"]
        lines += [f"tests/test_big.py::test_{n} PASSED" for n in range(20_000)]
        lines.append("FAILED tests/test_big.py::test_first - assert 1 == 2")
        lines += [f"tests/test_big.py::test_more_{n} PASSED" for n in range(29_998)]
        lines.append("FAILED tests/test_big.py::test_second - assert 3 == 4")
        lines.append("2 failed, 49998 passed")
        sys.stdout.write("\n".join(lines) + "\n")
        return 1
    if mode == "print-env":
        for name, value in sorted(os.environ.items()):
            print(f"{name}={value}")
        return 0
    if mode == "ansi":
        sys.stdout.flush()
        sys.stdout.buffer.write(
            b"\x1b[31mFAILED tests/a.py::test_red\x1b[0m - boom\r\nbad \xff byte\r\ndone\r\n"
        )
        return 1
    if mode == "marker":
        Path(sys.argv[2]).write_text("ran", encoding="utf-8")
        return 0
    raise SystemExit(f"unknown mode {mode!r}")


if __name__ == "__main__":
    sys.exit(main())
