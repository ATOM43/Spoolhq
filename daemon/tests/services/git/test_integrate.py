"""Integration mechanics: merge-in, markers, the squash, advancing main, tags, the guards."""

from pathlib import Path

import pytest

from spoolhq.services.git import (
    DirtyRepoError,
    WorktreeManager,
    advance,
    commit_message,
    commit_staged,
    conclude_merge,
    create_tag,
    ensure_main_ready,
    is_ancestor,
    is_junk,
    is_secret,
    merge_head,
    merge_in,
    outside_symlinks,
    restore_branch,
    start_squash,
    tag_exists,
    too_large,
    unresolved_files,
    unstage,
)
from tests.conftest import commit_file, run_git


def head(path: Path, rev: str = "HEAD") -> str:
    return run_git(path, "rev-parse", rev).strip()


# --- the commit message ---------------------------------------------------------------


def test_untrusted_title_becomes_one_line_of_at_most_72() -> None:
    title = "Fix\nthe\tthing " + "x" * 100

    message = commit_message("T04", title, None, 12)

    subject, rest = message.split("\n", 1)
    assert len(subject) <= 72
    assert subject.startswith("T04: Fix the thing xxx")
    assert "\t" not in subject
    # No progress note: no body paragraph, just the trailers.
    assert rest == "\nSpoolHQ-Ticket: T04\nSpoolHQ-Run: 12\n"


def test_progress_note_is_wrapped_at_72() -> None:
    note = "Added the parser. " * 10

    message = commit_message("T04", "Parser", note, 3)

    subject, body, trailers = message.rstrip("\n").split("\n\n")
    assert subject == "T04: Parser"
    assert all(len(line) <= 72 for line in body.splitlines())
    assert len(body.splitlines()) > 1
    assert trailers == "SpoolHQ-Ticket: T04\nSpoolHQ-Run: 3"


def test_control_characters_are_removed() -> None:
    assert commit_message("T04", "a\x00b\x1b[31mc\r\nd", None, 1).split("\n")[0] == (
        "T04: a b [31mc d"
    )


# --- the diff guard -------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "__pycache__/x.pyc",
        "pkg/__pycache__/m.cpython-312.pyc",
        "a.pyc",
        "node_modules/a.js",
        "web/node_modules/x/y.js",
        ".pytest_cache/v/cache",
        ".mypy_cache/3.12/x.json",
        ".ruff_cache/0.1/x",
        ".DS_Store",
        "docs/.ds_store",
        "spoolhq.egg-info/PKG-INFO",
        ".pnpm-store/v11/projects/92009e6764a75d37933b5affffd16167",
        "web/.pnpm-store/v11/index.json",
        ".yarn/cache/left-pad.zip",
        ".npm/_cacache/index",
    ],
)
def test_build_junk(path: str) -> None:
    assert is_junk(path)


@pytest.mark.parametrize(
    "path",
    [
        "hello.py",
        "src/node_modules.py",
        "pycache.md",
        "a.py",
        ".yarn/releases/yarn.cjs",
        ".npmrc.md",
    ],
)
def test_not_junk(path: str) -> None:
    assert not is_junk(path)


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        "app/.env.local",
        ".env.production",
        "cert.pem",
        "server.key",
        "a.p12",
        "a.pfx",
        "id_rsa",
        "id_rsa.pub",
        "id_ed25519",
        ".netrc",
        ".npmrc",
        ".pypirc",
        "config/credentials.json",
        "release.keystore",
        ".ssh/config",
        "home/.ssh/known_hosts",
        ".claude/settings.json",
    ],
)
def test_likely_secrets(path: str) -> None:
    assert is_secret(path)


@pytest.mark.parametrize("path", [".env.example", "app/.env.example", "env.py", "keys.md"])
def test_not_secrets(path: str) -> None:
    assert not is_secret(path)


def test_too_large(tmp_path: Path) -> None:
    (tmp_path / "small.txt").write_bytes(b"x" * 10)
    (tmp_path / "big.bin").write_bytes(b"x" * (6 * 1024 * 1024))

    assert too_large(tmp_path, ["small.txt", "gone.txt"]) is None
    assert too_large(tmp_path, ["small.txt", "big.bin"]) == ("big.bin", 6 * 1024 * 1024)


# --- the worktree ---------------------------------------------------------------------


@pytest.fixture
def branch(manager: WorktreeManager, wt_repo: Path) -> Path:
    """T04's worktree with one commit adding ``feature.py``."""
    wt = manager.create("T04", "Feature", 1)
    commit_file(wt.path, "feature.py", "x = 1\n", "feature")
    return wt.path


def test_merge_in_with_main_unchanged_is_a_no_op(branch: Path) -> None:
    before = head(branch)

    result = merge_in(branch, "main")

    assert (result.changed, result.conflicts) == (False, ())
    assert not merge_head(branch)
    assert head(branch) == before


def test_merge_in_brings_main_and_concludes(branch: Path, wt_repo: Path) -> None:
    moved = commit_file(wt_repo, "other.py", "y = 1\n", "other")

    result = merge_in(branch, "main")
    sha = conclude_merge(branch, "spool: merge main")

    assert (result.changed, result.conflicts) == (True, ())
    assert run_git(branch, "rev-parse", f"{sha}^2").strip() == moved
    assert (branch / "other.py").is_file()
    assert not merge_head(branch)


def test_conflict_leaves_the_worktree_mid_merge(branch: Path, wt_repo: Path) -> None:
    commit_file(wt_repo, "feature.py", "x = 2\n", "main's feature")

    result = merge_in(branch, "main")

    assert result.conflicts == ("feature.py",)
    assert merge_head(branch)
    assert "<<<<<<<" in (branch / "feature.py").read_text(encoding="utf-8")
    assert unresolved_files(branch, result.conflicts) == ("feature.py",)

    (branch / "feature.py").write_text("x = 3\n", encoding="utf-8")
    assert unresolved_files(branch, result.conflicts) == ()
    conclude_merge(branch, "spool: resolved")
    assert not merge_head(branch)


@pytest.mark.parametrize(
    "text", ["<<<<<<< ours\n", "a\n=======\nb\n", ">>>>>>> theirs\n", "<<<<<<<\n"]
)
def test_any_marker_line_counts(branch: Path, text: str) -> None:
    (branch / "feature.py").write_text(text, encoding="utf-8")

    assert unresolved_files(branch, ["feature.py"]) == ("feature.py",)


def test_marker_like_text_inside_a_line_is_fine(branch: Path) -> None:
    (branch / "feature.py").write_text('s = "<<<<<<< not a marker"\n# ========\n', "utf-8")

    assert unresolved_files(branch, ["feature.py"]) == ()


def test_squash_is_one_commit_on_main_and_keeps_the_branch(
    branch: Path, wt_repo: Path, manager: WorktreeManager
) -> None:
    main_sha = head(wt_repo, "main")
    commit_file(branch, "second.py", "z = 1\n", "second")
    (branch / "__pycache__").mkdir()
    (branch / "__pycache__" / "x.pyc").write_bytes(b"\0")
    run_git(branch, "add", "-A")
    run_git(branch, "commit", "--quiet", "-m", "junk")
    tip = head(branch)

    changed = start_squash(branch, main_sha)
    unstage(branch, main_sha, ["__pycache__/x.pyc"])
    sha = commit_staged(branch, "T04: Feature\n")

    assert sorted(changed) == ["__pycache__/x.pyc", "feature.py", "second.py"]
    assert head(branch, f"{sha}^") == main_sha
    files = run_git(branch, "show", "--name-only", "--format=", sha).split()
    assert sorted(files) == ["feature.py", "second.py"]
    assert (branch / "__pycache__" / "x.pyc").is_file()  # left on disk, not committed
    assert head(wt_repo, "refs/heads/feat/T04-feature") == tip  # the branch didn't move
    restore_branch(branch, "feat/T04-feature")
    assert run_git(branch, "symbolic-ref", "HEAD").strip() == "refs/heads/feat/T04-feature"


def test_restore_aborts_a_merge(branch: Path, wt_repo: Path) -> None:
    commit_file(wt_repo, "feature.py", "x = 2\n", "main's feature")
    merge_in(branch, "main")

    restore_branch(branch, "feat/T04-feature")

    assert not merge_head(branch)
    assert (branch / "feature.py").read_text(encoding="utf-8") == "x = 1\n"


# --- the main checkout ----------------------------------------------------------------


def _squash(branch: Path, main_sha: str) -> str:
    start_squash(branch, main_sha)
    return commit_staged(branch, "T04: Feature\n")


def test_advance_fast_forwards_the_checked_out_branch(branch: Path, wt_repo: Path) -> None:
    main_sha = head(wt_repo, "main")
    sha = _squash(branch, main_sha)

    assert advance(wt_repo, "main", sha, main_sha)

    assert head(wt_repo) == sha
    assert (wt_repo / "feature.py").is_file()
    assert run_git(wt_repo, "status", "--porcelain") == ""


def test_advance_refuses_a_dirty_checkout(branch: Path, wt_repo: Path) -> None:
    main_sha = head(wt_repo, "main")
    sha = _squash(branch, main_sha)
    (wt_repo / "notes.txt").write_text("mine\n", encoding="utf-8")

    with pytest.raises(DirtyRepoError):
        advance(wt_repo, "main", sha, main_sha)
    with pytest.raises(DirtyRepoError):
        ensure_main_ready(wt_repo, "main")
    assert head(wt_repo) == main_sha
    assert (wt_repo / "notes.txt").read_text(encoding="utf-8") == "mine\n"


def test_advance_reports_main_moved(branch: Path, wt_repo: Path) -> None:
    main_sha = head(wt_repo, "main")
    sha = _squash(branch, main_sha)
    moved = commit_file(wt_repo, "other.py", "y\n", "other")

    assert not advance(wt_repo, "main", sha, main_sha)
    assert head(wt_repo) == moved


def test_advance_with_update_ref_when_main_is_not_checked_out(branch: Path, wt_repo: Path) -> None:
    main_sha = head(wt_repo, "main")
    sha = _squash(branch, main_sha)
    run_git(wt_repo, "switch", "--quiet", "-c", "other")
    (wt_repo / "notes.txt").write_text("dirty is fine here\n", encoding="utf-8")

    ensure_main_ready(wt_repo, "main")  # main isn't checked out: nothing to check
    assert not advance(wt_repo, "main", sha, "0" * 40)
    assert head(wt_repo, "main") == main_sha
    assert advance(wt_repo, "main", sha, main_sha)
    assert head(wt_repo, "main") == sha
    assert run_git(wt_repo, "symbolic-ref", "HEAD").strip() == "refs/heads/other"


def test_tags(wt_repo: Path) -> None:
    sha = head(wt_repo)
    assert not tag_exists(wt_repo, "ticket/T04")

    create_tag(wt_repo, "ticket/T04", sha)
    create_tag(wt_repo, "ticket/T04", sha)  # again at the same commit: fine

    assert tag_exists(wt_repo, "ticket/T04")
    assert run_git(wt_repo, "cat-file", "-t", "ticket/T04").strip() == "commit"  # lightweight
    assert is_ancestor(wt_repo, sha, sha)


def _stage_link(worktree: Path, path: str, target: str) -> None:
    """Stage a symlink through the index, so the test needs no symlink support."""
    blob_file = worktree.parent / "link-target"
    blob_file.write_bytes(target.encode("utf-8"))
    blob = git_out(worktree, "hash-object", "-w", str(blob_file))
    run_git(worktree, "update-index", "--add", "--cacheinfo", f"120000,{blob},{path}")


def git_out(path: Path, *args: str) -> str:
    return run_git(path, *args).strip()


@pytest.mark.parametrize(
    ("path", "target"),
    [
        ("link", "/etc/passwd"),
        ("link", "C:\\Windows\\System32"),
        ("link", "../outside"),
        ("a/b/link", "../../../outside"),
        ("a/link", "../.."),
    ],
)
def test_symlinks_out_of_the_repo_are_found(
    branch: Path, wt_repo: Path, path: str, target: str
) -> None:
    main_sha = head(wt_repo, "main")
    _stage_link(branch, path, target)

    assert outside_symlinks(branch, main_sha) == [(path, target)]


@pytest.mark.parametrize(
    ("path", "target"),
    [
        ("link", "feature.py"),
        ("a/b/link", "../../feature.py"),
        (".pnpm-store/v11/projects/92009e6764a75d37933b5affffd16167", "../../../desktop"),
    ],
)
def test_symlinks_inside_the_repo_are_allowed(
    branch: Path, wt_repo: Path, path: str, target: str
) -> None:
    main_sha = head(wt_repo, "main")
    _stage_link(branch, path, target)

    assert outside_symlinks(branch, main_sha) == []
