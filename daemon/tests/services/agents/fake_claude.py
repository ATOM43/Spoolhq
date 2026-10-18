"""A stand-in for the ``claude`` CLI, run as a real subprocess by the adapter tests.

    python fake_claude.py --scenario <jsonl> --record <json> [options] <claude args...>

``--version`` prints ``--version-string``; ``auth status`` prints the login JSON (exit
1 with ``--logged-out``, unless ``ANTHROPIC_API_KEY`` is set: then ``api_key``).
Anything else is a run: it records its argv, environment variable names, stdin and
pid to ``--record``, prints the scenario's lines, then sleeps for ``--sleep`` seconds
(``--spawn-child`` first starts a child process that sleeps too, and records its pid)
and exits with ``--exit-code``. ``--ignore-sigint`` and ``--ignore-sigterm`` make the
run ignore those signals (POSIX), to test the adapter's stop sequence. With ``--stubs``,
every mode first creates empty stub files and folders in its cwd, as the real CLI does
with the env scrub on.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

OPTIONS_WITH_VALUE = {
    "--scenario",
    "--record",
    "--version-string",
    "--auth-method",
    "--sleep",
    "--exit-code",
}
FLAGS = {"--logged-out", "--spawn-child", "--stubs", "--ignore-sigint", "--ignore-sigterm"}
# What Claude Code 2.1.302 leaves in its cwd with CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1.
STUB_FILES = (".env", ".env.local", ".npmrc", "package.json", "yarn.lock")
STUB_DIRS = (".claude/agents", ".claude/commands", "node_modules/.bin")


def make_stubs() -> None:
    for name in STUB_FILES:
        if not os.path.lexists(name):
            Path(name).touch()
    for name in STUB_DIRS:
        Path(name).mkdir(parents=True, exist_ok=True)


def parse(argv: list[str]) -> tuple[dict[str, str], list[str]]:
    options: dict[str, str] = {}
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in OPTIONS_WITH_VALUE:
            options[arg] = argv[index + 1]
            index += 2
        elif arg in FLAGS:
            options[arg] = "1"
            index += 1
        else:
            break
    return options, argv[index:]


def main() -> int:
    options, claude_args = parse(sys.argv[1:])
    if "--stubs" in options:
        make_stubs()
    if claude_args == ["--version"]:
        print(f"{options.get('--version-string', '2.1.302')} (Claude Code)")
        return 0
    if claude_args[:2] == ["auth", "status"]:
        logged_out = "--logged-out" in options
        method = "none" if logged_out else options.get("--auth-method", "claude.ai")
        if logged_out and os.environ.get("ANTHROPIC_API_KEY"):
            logged_out, method = False, "api_key"
        print(json.dumps({"loggedIn": not logged_out, "authMethod": method}, indent=2))
        return 1 if logged_out else 0

    if "--ignore-sigint" in options:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    if "--ignore-sigterm" in options:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    stdin = sys.stdin.read()
    record: dict[str, object] = {
        "argv": claude_args,
        "env": sorted(os.environ),
        "stdin": stdin,
        "pid": os.getpid(),
    }
    child = None
    if "--spawn-child" in options:
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])  # noqa: S603
        record["child_pid"] = child.pid
    Path(options["--record"]).write_text(json.dumps(record), encoding="utf-8")

    for line in Path(options["--scenario"]).read_text(encoding="utf-8").splitlines():
        if line.strip():
            sys.stdout.write(line + "\n")
            sys.stdout.flush()
    print("fake claude: done", file=sys.stderr)
    time.sleep(float(options.get("--sleep", "0")))
    return int(options.get("--exit-code", "0"))


if __name__ == "__main__":
    sys.exit(main())
