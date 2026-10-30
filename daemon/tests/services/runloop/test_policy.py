"""services/runloop/policy.py: the matcher, the rules and the delivery mode (no git)."""

import pytest

from spoolhq.services.git import ChangedFile
from spoolhq.services.projects import DEFAULT_PROTECTED_PATHS
from spoolhq.services.runloop import (
    PolicyDecision,
    RuleHit,
    delivery_mode,
    describe,
    evaluate,
    path_matches,
)


def change(path: str, lines: int = 1, old: str | None = None) -> ChangedFile:
    return ChangedFile(path=path, old_path=old, added=lines, removed=0)


def decide(*changes: ChangedFile, **kwargs: object) -> PolicyDecision:
    args: dict[str, object] = {
        "review_required": False,
        "max_diff_lines": 400,
        "protected": DEFAULT_PROTECTED_PATHS,
        "reviewer_summary": None,
    }
    args.update(kwargs)
    return evaluate(changes=changes, **args)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("pattern", "path", "expected"),
    [
        ("**/migrations/**", "migrations/0001.py", True),
        ("**/migrations/**", "a/b/migrations/c/d.py", True),
        ("**/migrations/**", "migrationsx/a.py", False),
        ("**/migrations/**", "a/migrations", False),
        ("justfile", "justfile", True),
        ("justfile", "sub/justfile", False),
        ("**/CLAUDE.md", "CLAUDE.md", True),
        ("**/CLAUDE.md", "backend/CLAUDE.md", True),
        ("**/CLAUDE.md", "backend/claude.md", False),
        ("CLAUDE.md", "claude.md", False),
        (".github/**", ".github/workflows/ci.yml", True),
        (".github/**", "x/.github/ci.yml", False),
        ("docker-compose*.yml", "docker-compose.prod.yml", True),
        ("docker-compose*.yml", "deploy/docker-compose.yml", False),
        ("**/*auth*.py", "src/oauth_client.py", True),
        ("**/*auth*.py", "auth/x.txt", False),
        ("a?c", "abc", True),
        ("a?c", "a/c", False),
        ("a+b(c).py", "a+b(c).py", True),
        ("**", "any/thing", True),
    ],
)
def test_path_matches(pattern: str, path: str, expected: bool) -> None:
    assert path_matches(pattern, path) is expected


def test_no_rule_holds() -> None:
    assert decide(change("src/app.py", 400)) == PolicyDecision(False, ())


def test_every_rule_that_holds_is_listed() -> None:
    decision = decide(
        change("src/app.py", 500),
        change(".github/workflows/ci.yml"),
        review_required=True,
        reviewer_summary="  Unsure about\nthe schema.  ",
        hold=True,
    )
    assert decision.needs_human
    assert decision.rules == (
        RuleHit("needs_human", "Unsure about the schema."),
        RuleHit("review_required", "the ticket is marked review_required"),
        RuleHit("diff_size", "501 lines > 400"),
        RuleHit("protected_paths", ".github/workflows/ci.yml"),
        RuleHit("hold_mode", "run.integration is hold"),
    )
    assert describe(decision.rules) == (
        "needs you: needs_human (Unsure about the schema.), review_required (the ticket is "
        "marked review_required), diff_size (501 lines > 400), protected_paths "
        "(.github/workflows/ci.yml), hold_mode (run.integration is hold)"
    )


def test_the_reviewer_summary_is_cut_to_200_characters() -> None:
    (hit,) = decide(reviewer_summary="x" * 300).rules
    assert hit == RuleHit("needs_human", "x" * 200)
    (empty,) = decide(reviewer_summary="").rules
    assert empty == RuleHit("needs_human", "the reviewer asked for a person")


def test_more_than_ten_protected_paths_are_cut() -> None:
    paths = [f"backend/migrations/{i:04d}.py" for i in range(13)]
    (hit,) = decide(*(change(p) for p in paths)).rules
    assert hit == RuleHit("protected_paths", ", ".join(paths[:10]) + " and 3 more")


def test_lockfiles_count_toward_protected_paths_not_the_size() -> None:
    decision = decide(
        change("uv.lock", 5000), change("frontend/pnpm-lock.yaml", 900), change("a.py", 400)
    )
    assert decision.rules == (RuleHit("protected_paths", "uv.lock, frontend/pnpm-lock.yaml"),)


def test_the_size_is_added_plus_removed_and_binaries_are_zero() -> None:
    edited = ChangedFile("a.py", None, added=200, removed=201)
    binary = ChangedFile("logo.png", None, added=0, removed=0)
    assert decide(edited, binary).rules == (RuleHit("diff_size", "401 lines > 400"),)
    assert decide(edited, max_diff_lines=401).rules == ()


@pytest.mark.parametrize(
    ("old", "new"), [("src/x.py", ".github/x.py"), (".github/x.py", "src/x.py")]
)
def test_a_rename_hits_on_either_name(old: str, new: str) -> None:
    (hit,) = decide(change(new, 0, old=old)).rules
    assert hit == RuleHit("protected_paths", ".github/x.py")


def test_a_project_list_replaces_the_default() -> None:
    assert decide(change(".github/ci.yml"), protected=["docs/**"]).rules == ()
    (hit,) = decide(change("docs/a.md"), protected=["docs/**"]).rules
    assert hit.rule == "protected_paths"


def test_delivery_mode() -> None:
    nothing = PolicyDecision(False, ())
    sized = PolicyDecision(True, (RuleHit("diff_size", "401 lines > 400"),))
    held = PolicyDecision(True, (*sized.rules, RuleHit("hold_mode", "run.integration is hold")))
    assert delivery_mode(nothing, True) == delivery_mode(nothing, False) == "direct"
    assert delivery_mode(sized, True) == "pr"
    assert delivery_mode(sized, False) == "approval"
    assert delivery_mode(held, True) == delivery_mode(held, False) == "approval"


def test_describe_reads_stored_rules() -> None:
    assert describe([]) == ""
    assert describe([{"rule": "diff_size", "detail": "812 lines > 400"}]) == (
        "needs you: diff_size (812 lines > 400)"
    )
