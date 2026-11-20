"""New dependencies: names added to each manifest kind fire the rule; versions and
lockfiles don't; ``allow`` turns it off."""

from pathlib import Path

import pytest

from spoolhq.services.git import staged_changes
from spoolhq.services.runloop.dependencies import added_dependencies, manifest_names
from spoolhq.services.runloop.policy import evaluate
from tests.conftest import commit_file, run_git

pytestmark = pytest.mark.usefixtures("git_identity")

PYPROJECT = """\
[project]
name = "demo"
dependencies = ["fastapi==0.1", "SQLAlchemy[asyncio]>=2"]
[project.optional-dependencies]
docs = ["mkdocs"]
[dependency-groups]
dev = ["pytest>=8", {include-group = "lint"}]
lint = ["ruff"]
"""
CARGO = """\
[package]
name = "demo"
[dependencies]
serde = "1"
[dev-dependencies]
proptest = { version = "1" }
[workspace.dependencies]
tokio = "1"
"""
PACKAGE = '{"name": "x", "dependencies": {"react": "^18"}, "devDependencies": {"vitest": "1"}}'
REQUIREMENTS = "# pinned\nrequests==2.0  # http\n-r base.txt\n-e .\ngit+https://x/y.git\nattrs\n"


@pytest.mark.parametrize(
    ("name", "text", "names"),
    [
        ("pyproject.toml", PYPROJECT, {"fastapi", "sqlalchemy", "mkdocs", "pytest", "ruff"}),
        ("Cargo.toml", CARGO, {"serde", "proptest", "tokio"}),
        ("package.json", PACKAGE, {"react", "vitest"}),
        ("requirements-dev.txt", REQUIREMENTS, {"requests", "attrs"}),
        ("package.json", "{not json", set()),
        ("pyproject.toml", "[broken", set()),
    ],
)
def test_manifest_names(name: str, text: str, names: set[str]) -> None:
    assert manifest_names(name, text) == names


def staged(repo: Path, files: dict[str, str]) -> list[str]:
    base = run_git(repo, "rev-parse", "HEAD").strip()
    for name, text in files.items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(text, encoding="utf-8", newline="\n")
    run_git(repo, "add", "-A")
    return added_dependencies(repo, base, staged_changes(repo, base))


@pytest.mark.parametrize(
    ("name", "before", "after", "added"),
    [
        ("pyproject.toml", PYPROJECT, PYPROJECT.replace('"ruff"', '"ruff", "httpx"'), ["httpx"]),
        ("app/Cargo.toml", CARGO, CARGO + 'rand = "0.8"\n', ["rand"]),
        (
            "web/package.json",
            PACKAGE,
            PACKAGE.replace('"vitest"', '"left-pad": "1", "vitest"'),
            ["left-pad"],
        ),
        ("requirements.txt", REQUIREMENTS, REQUIREMENTS + "Flask>=3\n", ["flask"]),
    ],
)
def test_a_new_name_in_each_manifest_kind_is_found(
    git_repo: Path, name: str, before: str, after: str, added: list[str]
) -> None:
    (git_repo / name).parent.mkdir(exist_ok=True)
    commit_file(git_repo, name, before, "manifest")
    assert staged(git_repo, {name: after}) == added


def test_a_new_manifest_counts_all_its_names(git_repo: Path) -> None:
    assert staged(git_repo, {"package.json": PACKAGE}) == ["react", "vitest"]


def test_version_bumps_and_lockfile_only_changes_do_not_count(git_repo: Path) -> None:
    commit_file(git_repo, "requirements.txt", "requests==2.0\n", "manifest")
    commit_file(git_repo, "uv.lock", "a\n", "lock")
    assert staged(git_repo, {"requirements.txt": "requests==2.1\n", "uv.lock": "b\n"}) == []


def test_the_rule_names_the_dependencies_and_is_off_without_names() -> None:
    hit = evaluate(
        review_required=False,
        changes=[],
        max_diff_lines=400,
        protected=[],
        reviewer_summary=None,
        new_dependencies=["httpx", "rand"],
    )
    assert [(h.rule, h.detail) for h in hit.rules] == [("new_dependencies", "httpx, rand")]
    quiet = evaluate(
        review_required=False, changes=[], max_diff_lines=400, protected=[], reviewer_summary=None
    )
    assert not quiet.needs_human
