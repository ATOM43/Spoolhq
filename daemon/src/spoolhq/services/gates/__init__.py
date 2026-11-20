"""Gates: a project's install, lint and test commands, run in a worktree.

``run_gates`` runs them in order without a shell, in a scrubbed environment, with a
timeout that stops the whole process tree, streams each one's output to a capped log
and returns structured results with a trimmed excerpt and the failing test names.
``check_file_sizes`` is the built-in file-size gate the run loop adds after them.
``try_command`` runs one command once, for the app's **Test** button.
``check_done_when`` maps "Done when" items naming a configured command to its gate.
This package imports no other service. See ``docs/gates.md``.
"""

from spoolhq.services.gates.command import (
    SHELL_SYNTAX_ERROR,
    check_gate_command,
    gate_env,
    split_command,
)
from spoolhq.services.gates.model import (
    GATE_NAMES,
    DoneWhenCheck,
    GateFailureData,
    GateName,
    GateResult,
    GateRun,
    GateStatus,
)
from spoolhq.services.gates.output import first_failure, split_lines
from spoolhq.services.gates.runner import (
    DEFAULT_TIMEOUTS,
    check_done_when,
    run_gates,
    try_command,
)
from spoolhq.services.gates.size import (
    DEFAULT_EXEMPT,
    DEFAULT_MAX_FILE_LINES,
    FILE_SIZE,
    check_file_sizes,
    count_lines,
    is_exempt,
)

__all__ = [
    "DEFAULT_EXEMPT",
    "DEFAULT_MAX_FILE_LINES",
    "FILE_SIZE",
    "check_file_sizes",
    "count_lines",
    "is_exempt",
    "DEFAULT_TIMEOUTS",
    "GATE_NAMES",
    "SHELL_SYNTAX_ERROR",
    "DoneWhenCheck",
    "GateFailureData",
    "GateName",
    "GateResult",
    "GateRun",
    "GateStatus",
    "check_done_when",
    "check_gate_command",
    "first_failure",
    "gate_env",
    "run_gates",
    "split_command",
    "split_lines",
    "try_command",
]
