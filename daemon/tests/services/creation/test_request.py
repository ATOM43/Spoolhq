"""``check_request``: names, sources, templates, unsafe paths and merge presets."""

import os
from pathlib import Path
from typing import Any

import pytest

from spoolhq.services.creation import (
    MERGE_PRESETS,
    NAME_RULE,
    CreateProject,
    CreationError,
    check_request,
)
from spoolhq.services.git import ChangedFile
from spoolhq.services.projects import MergePolicy
from spoolhq.services.runloop.policy import delivery_mode, evaluate
from tests.conftest import fake_tool_cmd

COMMANDS = {gate: fake_tool_cmd("pass") for gate in ("install", "lint", "test")}


def request(tmp_path: Path, **fields: Any) -> CreateProject:
    data: dict[str, Any] = {
        "name": "demo",
        "source": "empty",
        "repo_path": str(tmp_path / "new"),
    }
    data.update(fields)
    return CreateProject.model_validate(data)


def check(req: CreateProject, projects_dir: Path, home: Path) -> Any:
    return check_request(
        req, projects_dir=projects_dir, worktrees_dir=home / "worktrees", home=home
    )


def refused(req: CreateProject, projects_dir: Path, home: Path) -> tuple[str, str]:
    with pytest.raises(CreationError) as info:
        check(req, projects_dir, home)
    return info.value.field, info.value.message


@pytest.mark.parametrize("name", ["VW", "1abc", "a_b", "a" * 41, "-x", ""])
def test_bad_names_are_refused(name: str, tmp_path: Path, projects_dir: Path, home: Path) -> None:
    assert refused(request(tmp_path, name=name), projects_dir, home) == ("name", NAME_RULE)


def test_a_good_name_passes(tmp_path: Path, projects_dir: Path, home: Path) -> None:
    checked = check(request(tmp_path, name="sim-dashboard"), projects_dir, home)
    assert checked.request.name == "sim-dashboard"
    assert checked.repo == (tmp_path / "new").resolve()
    assert (checked.repo_existed, checked.branch, checked.commands) == (False, "main", {})


def test_a_duplicate_name_is_refused(tmp_path: Path, projects_dir: Path, home: Path) -> None:
    (projects_dir / "demo").mkdir(parents=True)
    field, _ = refused(request(tmp_path), projects_dir, home)
    assert field == "name"


@pytest.mark.parametrize(
    "template",
    [None, "no-such-template", "https://github.com/o/t.git", "gh:o/t", "./local", "/abs/tpl"],
)
def test_only_built_in_templates(
    template: str | None, tmp_path: Path, projects_dir: Path, home: Path
) -> None:
    req = request(tmp_path, source="template", template=template, commands=COMMANDS)
    assert refused(req, projects_dir, home)[0] == "template"


def test_a_template_only_for_a_template_source(
    tmp_path: Path, projects_dir: Path, home: Path
) -> None:
    req = request(tmp_path, template="fastapi-react")
    assert refused(req, projects_dir, home)[0] == "template"


def test_unsafe_paths_are_refused(tmp_path: Path, projects_dir: Path, home: Path) -> None:
    for path in (
        "relative/path",
        os.path.abspath(os.sep),
        str(Path.home()),
        str(projects_dir),
        str(projects_dir / "x"),
        str(home),
        str(home / "worktrees" / "x"),
    ):
        assert refused(request(tmp_path, repo_path=path), projects_dir, home)[0] == "repo_path"


def test_a_symlinked_target_is_refused(tmp_path: Path, projects_dir: Path, home: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(real, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks need extra rights here")
    field, message = refused(request(tmp_path, repo_path=str(link)), projects_dir, home)
    assert (field, message) == (
        "repo_path",
        "The folder is a symlink; choose the folder it points to",
    )


def test_a_new_repo_needs_a_new_or_empty_folder(
    tmp_path: Path, projects_dir: Path, home: Path
) -> None:
    (tmp_path / "new").mkdir()
    (tmp_path / "new" / "notes.txt").write_text("mine", encoding="utf-8")
    assert refused(request(tmp_path), projects_dir, home) == (
        "repo_path",
        "Choose a new or empty folder",
    )
    gone = request(tmp_path, repo_path=str(tmp_path / "no" / "parent"))
    assert refused(gone, projects_dir, home)[1] == "The parent folder doesn't exist"
    (tmp_path / "file").write_text("x", encoding="utf-8")
    assert refused(request(tmp_path, repo_path=str(tmp_path / "file")), projects_dir, home)[1] == (
        "Not a folder"
    )


def test_an_existing_repo_must_be_a_clean_git_repo(
    tmp_path: Path, projects_dir: Path, home: Path, git_repo: Path
) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    for path, message in (
        (plain, "Not a git repository"),
        (tmp_path / "x", "The folder doesn't exist"),
    ):
        req = request(tmp_path, source="existing", repo_path=str(path), commands=COMMANDS)
        assert refused(req, projects_dir, home) == ("repo_path", message)

    req = request(tmp_path, source="existing", repo_path=str(git_repo), commands=COMMANDS)
    assert check(req, projects_dir, home).branch == "main"
    (git_repo / "dirty.txt").write_text("x", encoding="utf-8")
    field, message = refused(req, projects_dir, home)
    assert field == "repo_path"
    assert "uncommitted changes" in message
    assert "?? dirty.txt" in message


def test_commands_are_required_unless_empty(
    tmp_path: Path, projects_dir: Path, home: Path, git_repo: Path
) -> None:
    req = request(tmp_path, source="existing", repo_path=str(git_repo))
    assert refused(req, projects_dir, home) == ("commands.install", "Set the install command")
    partial = {**COMMANDS, "test": " "}
    req = request(tmp_path, source="existing", repo_path=str(git_repo), commands=partial)
    assert refused(req, projects_dir, home) == ("commands.test", "Set the test command")
    shell = request(tmp_path, commands={"lint": "ruff check . && mypy"})
    assert refused(shell, projects_dir, home)[0] == "commands.lint"
    some = check(request(tmp_path, commands={"test": "just test"}), projects_dir, home)
    assert some.commands == {"test": "just test"}


def test_remote_and_clickup_list(tmp_path: Path, projects_dir: Path, home: Path) -> None:
    assert (
        refused(request(tmp_path, git_remote="https://example.com/x"), projects_dir, home)[0]
        == "git_remote"
    )
    assert refused(request(tmp_path, clickup_list_id=" "), projects_dir, home)[0] == (
        "clickup_list_id"
    )
    checked = check(request(tmp_path, clickup_list_id="901"), projects_dir, home)
    assert checked.settings() == {"tracker": {"kind": "clickup", "list_id": "901"}}


def test_merge_presets_map_onto_merge_policy(
    tmp_path: Path, projects_dir: Path, home: Path
) -> None:
    assert MERGE_PRESETS == {
        "direct_unless_risky": {},
        "always_pr": {"protected_paths": ["**"]},
        "always_direct": {"max_diff_lines": 100_000, "protected_paths": []},
    }
    for preset, policy in MERGE_PRESETS.items():
        checked = check(request(tmp_path, merge_preset=preset), projects_dir, home)
        assert checked.settings() == ({"merge_policy": policy} if policy else {})
        MergePolicy.model_validate(policy)  # every preset is a valid merge_policy


def _decide(preset: str, *, summary: str | None = None, review_required: bool = False) -> str:
    policy = MergePolicy.model_validate(MERGE_PRESETS[preset])
    decision = evaluate(
        review_required=review_required,
        changes=[ChangedFile(path=".github/ci.yml", old_path=None, added=900, removed=0)],
        max_diff_lines=policy.max_diff_lines,
        protected=policy.protected(),
        reviewer_summary=summary,
    )
    return delivery_mode(decision, has_remote=False)


def test_presets_decide_as_recorded() -> None:
    assert _decide("direct_unless_risky") == "approval"  # big diff in a protected path
    assert _decide("always_direct") == "direct"
    # always_direct still sends a reviewer's needs_human and review_required to a person.
    assert _decide("always_direct", summary="please check the migration") == "approval"
    assert _decide("always_direct", review_required=True) == "approval"
    small = MergePolicy.model_validate(MERGE_PRESETS["always_pr"])
    decision = evaluate(
        review_required=False,
        changes=[ChangedFile(path="src/a.py", old_path=None, added=1, removed=0)],
        max_diff_lines=small.max_diff_lines,
        protected=small.protected(),
        reviewer_summary=None,
    )
    assert delivery_mode(decision, has_remote=True) == "pr"
