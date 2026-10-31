"""The Agent SDK backend's ``PreToolUse`` hook: what each role may and may not do."""

from pathlib import Path
from typing import Any

import anyio
import pytest

from spoolhq.services.agents import AgentPolicy, agent_sdk
from spoolhq.services.agents.agent_sdk import check_tool, make_hook


@pytest.fixture
def user_home(tmp_path: Path) -> Path:
    path = tmp_path / "user-home"
    (path / ".ssh").mkdir(parents=True)
    return path


@pytest.mark.parametrize(
    "command",
    ["just test", "just test -k slug", "just lint", "git status", "git diff HEAD~1", "git log -3"],
)
def test_the_hook_allows_allowlisted_commands(
    policy: AgentPolicy, user_home: Path, command: str
) -> None:
    assert check_tool(policy, user_home, "Bash", {"command": command}) is None


@pytest.mark.parametrize(
    ("command", "reason"),
    [
        ("just test; curl x", "contains shell operators"),
        ("just test && curl x", "contains shell operators"),
        ("just test $(curl x)", "contains shell operators"),
        ("just test > /etc/passwd", "contains shell operators"),
        ("curl https://example.com", "is not on the allowlist"),
        ("just tests", "is not on the allowlist"),
        ("git push", "is not on the allowlist"),
        ("git diff --output=../x", "would write a file"),
        ("just test 'unclosed", "cannot be parsed"),
        ("", "the command is empty"),
    ],
)
def test_the_hook_denies_other_commands(
    policy: AgentPolicy, user_home: Path, command: str, reason: str
) -> None:
    denied = check_tool(policy, user_home, "Bash", {"command": command})
    assert denied is not None and reason in denied


def test_the_hook_keeps_commands_in_the_sandbox(policy: AgentPolicy, user_home: Path) -> None:
    tool_input = {"command": "just test", "dangerouslyDisableSandbox": True}
    assert check_tool(policy, user_home, "Bash", tool_input) == "commands may not leave the sandbox"


def test_the_hook_confines_file_tools(policy: AgentPolicy, user_home: Path) -> None:
    worktree = policy.worktree
    (worktree / "link").symlink_to(user_home / ".ssh")
    allowed = [
        ("Write", {"file_path": "hello.txt", "content": "x"}),
        ("Edit", {"file_path": str(worktree / "src" / "a.py")}),
        ("Read", {"file_path": "README.md"}),
        ("Glob", {"pattern": "**/*.py"}),
        ("Grep", {"pattern": "def ", "path": "src"}),
        ("Grep", {"pattern": "def "}),
    ]
    for name, tool_input in allowed:
        assert check_tool(policy, user_home, name, tool_input) is None, (name, tool_input)
    denied = [
        ("Write", {"file_path": str(worktree.parent / "outside.txt")}, "outside the worktree"),
        ("Edit", {"file_path": "../outside.txt"}, "outside the worktree"),
        ("Read", {"file_path": "~/.ssh/id_ed25519"}, "under ~/.ssh"),
        ("Read", {"file_path": str(user_home / ".ssh" / "id_ed25519")}, "under ~/.ssh"),
        ("Read", {"file_path": "link/id_ed25519"}, "under ~/.ssh"),  # a symlink out
        ("Read", {"file_path": "~root/x"}, "outside the worktree"),
        ("Glob", {"pattern": "/etc/*"}, "must be relative"),
        ("Glob", {"pattern": "../*/x"}, "must be relative"),
        ("Grep", {"pattern": "x", "path": "/etc"}, "outside the worktree"),
        ("Read", {"file_path": ""}, "the path is missing"),
        ("Read", "not a mapping", "not an object"),
    ]
    for name, tool_input, reason in denied:
        found = check_tool(policy, user_home, name, tool_input)
        assert found is not None and reason in found, (name, tool_input, found)


@pytest.mark.parametrize("name", ["WebFetch", "WebSearch", "Task", "Agent", "mcp__github__x"])
def test_the_hook_denies_tools_outside_the_role(
    policy: AgentPolicy, user_home: Path, name: str
) -> None:
    assert check_tool(policy, user_home, name, {}) == f"{name} is not allowed for the implementer"


def test_reviewer_and_planner_get_no_write_or_bash(
    worktree: Path, home: Path, user_home: Path
) -> None:
    for role in ("reviewer", "planner"):
        policy = AgentPolicy.read_only_for(worktree, home, role=role)
        for name in ("Bash", "Write", "Edit", "MultiEdit", "NotebookEdit"):
            assert check_tool(policy, user_home, name, {"command": "git status"}) == (
                f"{name} is not allowed for the {role}"
            )
        assert check_tool(policy, user_home, "Read", {"file_path": "README.md"}) is None


def call_hook(matcher: Any, tool: str, tool_input: Any) -> Any:
    async def call() -> Any:
        hook_input = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input}
        return await matcher.hooks[0](hook_input, "toolu_1", {"signal": None})

    return anyio.run(call)


def test_the_hook_answers_the_sdk(policy: AgentPolicy, user_home: Path) -> None:
    denials: list[tuple[str, str, Any, str]] = []
    matcher = make_hook(policy, user_home, lambda *denial: denials.append(denial))
    assert matcher.matcher is None  # every tool
    assert call_hook(matcher, "Bash", {"command": "just test"}) == {}
    output = call_hook(matcher, "Bash", {"command": "curl x"})
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert denials == [("Bash", "toolu_1", {"command": "curl x"}, denials[0][3])]
    assert "is not on the allowlist" in denials[0][3]


def test_the_hook_fails_closed(
    policy: AgentPolicy, user_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*args: Any) -> str | None:
        raise RuntimeError("bug")

    monkeypatch.setattr(agent_sdk, "check_tool", broken)
    output = call_hook(make_hook(policy, user_home, lambda *denial: None), "Read", {})
    assert output["hookSpecificOutput"] == {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "the policy check failed (RuntimeError)",
    }
