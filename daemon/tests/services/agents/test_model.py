"""AgentPolicy validation and the permission rules it produces."""

from pathlib import Path

import pytest

from spoolhq.services.agents import READ_ONLY_GIT, AgentPolicy, Budget, PolicyError
from spoolhq.services.agents.model import CREDENTIAL_PATHS, home_denials


def test_command_becomes_exact_and_prefix_rules(worktree: Path, home: Path) -> None:
    policy = AgentPolicy.for_worktree(worktree, {"test": "just test"}, home)
    assert policy.allowed_commands == ("just test",)
    assert policy.bash_rules()[:2] == ("Bash(just test)", "Bash(just test *)")


def test_read_only_git_follows_stack_commands(worktree: Path, home: Path) -> None:
    policy = AgentPolicy.for_worktree(worktree, {"lint": "just lint", "test": "just lint"}, home)
    assert (
        policy.read_only_git
        == READ_ONLY_GIT
        == (
            "git status",
            "git diff",
            "git log",
            "git show",
        )
    )
    # A command listed twice gives its rules once.
    assert policy.bash_rules() == (
        "Bash(just lint)",
        "Bash(just lint *)",
        "Bash(git status)",
        "Bash(git status *)",
        "Bash(git diff)",
        "Bash(git diff *)",
        "Bash(git log)",
        "Bash(git log *)",
        "Bash(git show)",
        "Bash(git show *)",
    )


def test_extra_stack_commands_are_allowed(worktree: Path, home: Path) -> None:
    commands = {"install": "uv sync", "lint": "ruff check", "test": "pytest", "e2e": "pnpm e2e"}
    policy = AgentPolicy.for_worktree(worktree, commands, home)
    assert policy.allowed_commands == ("uv sync", "ruff check", "pytest", "pnpm e2e")


@pytest.mark.parametrize(
    "command",
    [
        "just test; rm -rf ~",
        "just test && x",
        "just $(x)",
        "just test *",
        "just test | tee out",
        "just test > out",
        "just `x`",
        "just test\nrm -rf ~",
        "just test ?",
        "just [a]",
        "just {a,b}",
        "just test \\",
    ],
)
def test_shell_operators_and_wildcards_are_refused(
    worktree: Path, home: Path, command: str
) -> None:
    with pytest.raises(PolicyError) as exc:
        AgentPolicy.for_worktree(worktree, {"install": "just install", "test": command}, home)
    assert str(exc.value) == (
        f"commands.test: {command!r} contains shell operators or wildcards; use a plain command"
    )


def test_exact_message_from_the_ticket(worktree: Path, home: Path) -> None:
    with pytest.raises(PolicyError, match=r"^commands\.test: 'just test; rm -rf ~' contains"):
        AgentPolicy.for_worktree(worktree, {"test": "just test; rm -rf ~"}, home)


@pytest.mark.parametrize("command", [" just test", "just test ", "\tjust test"])
def test_surrounding_spaces_are_refused(worktree: Path, home: Path, command: str) -> None:
    with pytest.raises(PolicyError, match=r"^commands\.lint: .* leading or trailing spaces"):
        AgentPolicy.for_worktree(worktree, {"lint": command}, home)


@pytest.mark.parametrize("command", ["", "   "])
def test_empty_command_is_refused(worktree: Path, home: Path, command: str) -> None:
    with pytest.raises(PolicyError, match=r"^commands\.install: must not be empty$"):
        AgentPolicy.for_worktree(worktree, {"install": command}, home)


def test_relative_worktree_is_refused(home: Path) -> None:
    with pytest.raises(PolicyError, match="must be an absolute path"):
        AgentPolicy.for_worktree(Path("wt"), {"test": "just test"}, home)


def test_worktree_containing_the_spoolhq_home_is_refused(tmp_path: Path, home: Path) -> None:
    with pytest.raises(PolicyError, match="must not contain the SpoolHQ home"):
        AgentPolicy.for_worktree(tmp_path, {"test": "just test"}, home)
    with pytest.raises(PolicyError, match="must not contain the SpoolHQ home"):
        AgentPolicy.for_worktree(home, {"test": "just test"}, home)


def test_denied_paths_are_the_credentials_and_the_spoolhq_home(worktree: Path, home: Path) -> None:
    policy = AgentPolicy.for_worktree(worktree, {"test": "just test"}, home)
    assert policy.denied_read_paths == (*CREDENTIAL_PATHS, str(home.resolve()))
    assert policy.network_domains == ()


def test_worktree_inside_the_home_keeps_its_own_path_readable(home: Path) -> None:
    # The default layout: <home>/worktrees/<project>/<ticket>.
    worktree = home / "worktrees" / "demo" / "T01"
    worktree.mkdir(parents=True)
    (home / "worktrees" / "demo" / "T02").mkdir()
    (home / "worktrees" / "other").mkdir()
    (home / "logs").mkdir()
    (home / "token").write_text("secret", encoding="utf-8")
    (home / "config.toml").write_text("", encoding="utf-8")
    root = home.resolve()
    assert home_denials(home, worktree) == (
        str(root / "token"),
        str(root / "config.toml"),
        str(root / "logs"),
        str(root / "worktrees" / "other"),
        str(root / "worktrees" / "demo" / "T02"),
    )


def test_token_is_denied_even_before_it_exists(home: Path) -> None:
    worktree = home / "worktrees" / "demo" / "T01"
    assert home_denials(home, worktree) == (str(home.resolve() / "token"),)


def test_budget_defaults_to_thirty_minutes() -> None:
    assert Budget(max_turns=30, max_usd=None, max_tokens=None).timeout_s == 1800
