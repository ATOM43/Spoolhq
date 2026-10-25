"""services/templates/sources.py: built-in names, local folders and git URLs."""

from pathlib import Path

import pytest

from spoolhq.services.templates import (
    TemplateError,
    is_git_url,
    open_template,
)
from tests.conftest import make_git_template, make_template, run_git


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


def test_a_local_git_work_tree_records_its_head(tmp_path: Path) -> None:
    folder = make_template(tmp_path / "my-tpl")
    run_git(folder, "init", "--quiet", "--initial-branch=main")
    run_git(folder, "add", "--all")
    run_git(
        folder,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@example.invalid",
        "commit",
        "--quiet",
        "--no-verify",
        "-m",
        "t",
    )
    head = run_git(folder, "rev-parse", "HEAD").strip()
    with open_template(str(folder)) as template:
        assert (template.ref, template.vcs_ref) == (head, "HEAD")


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
    with pytest.raises(TemplateError, match="--template-ref only applies to a git URL"):
        with open_template("fastapi-react", "main"):
            pass
