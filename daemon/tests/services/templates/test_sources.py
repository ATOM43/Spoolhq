"""services/templates/sources.py: built-in names, local folders and git URLs."""

from pathlib import Path

import pytest

import spoolhq
from spoolhq.services.templates import (
    TemplateError,
    builtin_descriptions,
    builtin_names,
    is_git_url,
    open_template,
)
from tests.conftest import (
    commit_file,
    make_git_template,
    make_template,
    run_git,
    set_identity,
)


def test_fastapi_react_is_built_in() -> None:
    assert "fastapi-react" in builtin_names()
    descriptions = dict(builtin_descriptions())
    assert "FastAPI backend and a React frontend" in descriptions["fastapi-react"]


def test_a_built_in_records_the_package_version() -> None:
    with open_template("fastapi-react") as template:
        assert (template.kind, template.label, template.source) == (
            "builtin",
            "fastapi-react",
            "fastapi-react",
        )
        assert template.ref == spoolhq.__version__
        assert (template.root / "spoolhq-template.yaml").is_file()


def test_an_unknown_name() -> None:
    with pytest.raises(TemplateError) as info, open_template("nope"):
        pass
    assert (
        str(info.value) == "unknown template 'nope'; spool templates list shows the built-in ones"
    )


@pytest.mark.parametrize(
    "source",
    [
        "https://github.com/me/tpl",
        "ssh://git@host/tpl",
        "git@github.com:me/tpl.git",
        "file:///srv/tpl",
        "/srv/tpl.git",
        "gh:me/tpl",
    ],
)
def test_git_urls(source: str) -> None:
    assert is_git_url(source)


@pytest.mark.parametrize("source", ["fastapi-react", "./tpl", "/srv/tpl", "~/tpl"])
def test_not_git_urls(source: str) -> None:
    assert not is_git_url(source)


def test_a_local_folder(tmp_path: Path) -> None:
    folder = make_template(tmp_path / "my-tpl")
    with open_template(str(folder)) as template:
        assert (template.kind, template.label, template.ref) == ("local", "my-tpl", None)
        assert template.source == str(folder.resolve())


def test_a_local_git_repository_is_cloned_at_head(tmp_path: Path) -> None:
    url, head = make_git_template(tmp_path)
    folder = Path(url).parent / "template-work"
    (folder / "uncommitted.txt").write_text("x", encoding="utf-8")
    with open_template(str(folder)) as template:
        assert (template.kind, template.label, template.ref) == ("git", "template-work", head)
        assert template.source == str(folder.resolve())
        assert template.root != folder.resolve()
        assert not (template.root / ".git").exists()
        assert not (template.root / "uncommitted.txt").exists()


def test_a_local_git_repository_at_a_ref(tmp_path: Path) -> None:
    url, first = make_git_template(tmp_path)
    folder = Path(url).parent / "template-work"
    run_git(folder, "tag", "v1", first)
    set_identity(folder)
    commit_file(folder, "later.txt", "x\n", "later")
    with open_template(str(folder), "v1") as template:
        assert template.ref == first


def test_a_missing_local_folder(tmp_path: Path) -> None:
    with pytest.raises(TemplateError, match="template folder not found"):
        with open_template(str(tmp_path / "missing")):
            pass


def test_a_git_url_is_resolved_to_a_commit_and_cleaned_up(tmp_path: Path) -> None:
    url, commit = make_git_template(tmp_path)
    with open_template(url) as template:
        assert (template.kind, template.label, template.ref) == ("git", "template", commit)
        assert (template.root / "spoolhq-template.yaml").is_file()
        clone = template.root
    assert not clone.exists()


def test_a_git_ref(tmp_path: Path) -> None:
    url, commit = make_git_template(tmp_path)
    run_git(Path(url), "tag", "v1", commit)
    with open_template(url, "v1") as template:
        assert template.ref == commit


def test_an_unknown_git_ref(tmp_path: Path) -> None:
    url, _ = make_git_template(tmp_path)
    with pytest.raises(TemplateError, match="template 'template': cannot fetch ref 'nope'"):
        with open_template(url, "nope"):
            pass


@pytest.mark.parametrize("ref", ["--upload-pack=x", " "])
def test_a_bad_ref_is_refused(ref: str) -> None:
    with pytest.raises(TemplateError, match="invalid --template-ref"):
        with open_template("https://example.com/t.git", ref):
            pass


def test_a_ref_without_a_git_url() -> None:
    with pytest.raises(TemplateError, match="--template-ref only applies to a git template"):
        with open_template("fastapi-react", "main"):
            pass
