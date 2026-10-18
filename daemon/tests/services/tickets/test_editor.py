import shlex
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from spoolhq.cli import app
from spoolhq.services.tickets import TicketError, editor_command, run_editor, start_edit

runner = CliRunner()

FILE_NAME = "T01-first.md"
TICKET = """\
---
id: T01
title: First ticket  # keep me
phase: 0
status: ready
estimate_h: 1
---

## Done when
- [ ] It works
"""

# A stand-in editor: `python fake_editor.py <mode> <file>` rewrites the file and exits.
FAKE_EDITOR = """\
import pathlib
import re
import sys

mode, path = sys.argv[1], pathlib.Path(sys.argv[2])
text = path.read_text(encoding="utf-8")
if mode == "toggle":
    # Invalid on the first run, valid on the next one.
    state = pathlib.Path(__file__).with_suffix(".state")
    mode = "valid" if state.exists() else "invalid"
    state.touch()
if mode == "valid":
    path.write_text(re.sub("status: [a-z]+", "status: done", text), encoding="utf-8")
elif mode == "invalid":
    path.write_text(re.sub("status: [a-z]+", "status: doing", text), encoding="utf-8")
elif mode == "no-done-when":
    path.write_text(text.split("## Done when")[0], encoding="utf-8")
elif mode == "fail":
    sys.exit(3)
"""


def make_ticket(projects_dir: Path, text: str = TICKET) -> Path:
    tickets = projects_dir / "demo" / "tickets"
    tickets.mkdir(parents=True)
    path = tickets / FILE_NAME
    path.write_text(text, encoding="utf-8", newline="")
    return path


@pytest.fixture
def fake_editor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[[str], None]:
    script = tmp_path / "fake_editor.py"
    script.write_text(FAKE_EDITOR, encoding="utf-8")

    def use(mode: str) -> None:
        # Quoted the same way on every platform; Windows splitting strips the quotes.
        monkeypatch.setenv("EDITOR", f'"{sys.executable}" "{script}" {mode}')
        monkeypatch.delenv("VISUAL", raising=False)

    return use


# Choosing the editor ------------------------------------------------------------------


def test_visual_wins_over_editor() -> None:
    env = {"VISUAL": "code --wait", "EDITOR": "vim"}
    assert editor_command(env, windows=False) == ["code", "--wait"]


def test_editor_when_visual_is_blank() -> None:
    assert editor_command({"VISUAL": "  ", "EDITOR": "vim -n"}, windows=False) == ["vim", "-n"]


def test_fallback_editors() -> None:
    assert editor_command({}, windows=False) == ["nano"]
    assert editor_command({"EDITOR": '""'}, windows=False) == ["nano"]
    assert editor_command({}, windows=True) == ["notepad"]


def test_posix_quoting() -> None:
    env = {"EDITOR": "'/opt/My Editor/bin/ed' --flag \"two words\""}
    assert editor_command(env, windows=False) == ["/opt/My Editor/bin/ed", "--flag", "two words"]


def test_windows_paths_keep_backslashes() -> None:
    env = {"EDITOR": '"C:\\Program Files\\Notepad++\\notepad++.exe" -multiInst'}
    assert editor_command(env, windows=True) == [
        "C:\\Program Files\\Notepad++\\notepad++.exe",
        "-multiInst",
    ]


def test_shell_syntax_is_not_interpreted() -> None:
    env = {"EDITOR": "vim; rm -rf ~ && echo $HOME"}
    assert editor_command(env, windows=False) == ["vim;", "rm", "-rf", "~", "&&", "echo", "$HOME"]


def test_unbalanced_quote() -> None:
    with pytest.raises(TicketError, match="cannot read \\$EDITOR"):
        editor_command({"EDITOR": "'vim"}, windows=False)


def test_default_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VISUAL", "my-editor")
    assert editor_command()[0] == "my-editor"


def test_missing_editor(tmp_path: Path) -> None:
    with pytest.raises(TicketError, match="editor 'no-such-editor-xyz' not found"):
        run_editor(["no-such-editor-xyz"], tmp_path / "x.md")


@pytest.mark.skipif(sys.platform == "win32", reason="Windows has no executable bit")
def test_editor_that_cannot_start(tmp_path: Path) -> None:
    fake = tmp_path / "not-an-editor"
    fake.write_text("plain text, no shebang", encoding="utf-8")
    fake.chmod(0o755)
    with pytest.raises(TicketError, match="cannot start the editor"):
        run_editor([str(fake)], tmp_path / "x.md")


# The editing session ------------------------------------------------------------------


def test_start_edit_backs_up_and_restores(projects_dir: Path) -> None:
    path = make_ticket(projects_dir)
    edit = start_edit("demo", "T01", projects_dir=projects_dir, environ={"EDITOR": "vim"})
    assert edit.command == ["vim"]
    assert edit.backup == path.with_name(f".{FILE_NAME}.bak")
    assert edit.backup.read_text("utf-8") == TICKET

    path.write_text("broken", encoding="utf-8")
    with pytest.raises(TicketError, match="must start with a '---' line"):
        edit.check()
    edit.restore()
    assert path.read_text("utf-8") == TICKET
    assert not edit.backup.exists()


def test_check_reports_a_deleted_file(projects_dir: Path) -> None:
    path = make_ticket(projects_dir)
    edit = start_edit("demo", "T01", projects_dir=projects_dir, environ={})
    path.unlink()
    with pytest.raises(TicketError, match="not found at"):
        edit.check()
    edit.finish()
    assert not edit.backup.exists()


def test_invalid_ticket_can_be_edited(projects_dir: Path) -> None:
    make_ticket(projects_dir, TICKET.replace("status: ready", "status: doing"))
    edit = start_edit("demo", "T01", projects_dir=projects_dir, environ={})
    assert edit.path.name == FILE_NAME


# `spool tickets edit` with a fake editor ----------------------------------------------


@pytest.mark.integration
def test_edit_valid(projects_dir: Path, fake_editor: Callable[[str], None]) -> None:
    path = make_ticket(projects_dir)
    fake_editor("valid")
    result = runner.invoke(app, ["tickets", "edit", "demo", "T01"])
    assert result.exit_code == 0, result.output
    assert result.output == f"Saved tickets/{FILE_NAME}.\n"
    assert path.read_text("utf-8") == TICKET.replace("status: ready", "status: done")
    assert not path.with_name(f".{FILE_NAME}.bak").exists()


@pytest.mark.integration
def test_edit_invalid_restores_the_backup(
    projects_dir: Path, fake_editor: Callable[[str], None]
) -> None:
    path = make_ticket(projects_dir)
    before = path.read_bytes()
    fake_editor("invalid")
    result = runner.invoke(app, ["tickets", "edit", "demo", "T01"], input="n\n")
    assert result.exit_code == 1
    assert (
        f"tickets/{FILE_NAME}: status: must be one of draft, ready, running, "
        "awaiting_approval, blocked, done\n" in result.output
    )
    assert "The ticket is invalid. Reopen the editor? [Y/n]: n\n" in result.output
    assert result.output.endswith(f"Restored the previous version of tickets/{FILE_NAME}.\n")
    assert path.read_bytes() == before
    assert not path.with_name(f".{FILE_NAME}.bak").exists()


@pytest.mark.integration
def test_edit_invalid_then_reopen(projects_dir: Path, fake_editor: Callable[[str], None]) -> None:
    path = make_ticket(projects_dir)
    fake_editor("toggle")
    result = runner.invoke(app, ["tickets", "edit", "demo", "T01"], input="\n")
    assert result.exit_code == 0, result.output
    assert "status: must be one of" in result.output
    assert result.output.endswith(f"Saved tickets/{FILE_NAME}.\n")
    assert "status: done" in path.read_text("utf-8")


@pytest.mark.integration
def test_edit_aborted_prompt_restores(
    projects_dir: Path, fake_editor: Callable[[str], None]
) -> None:
    path = make_ticket(projects_dir)
    fake_editor("invalid")
    result = runner.invoke(app, ["tickets", "edit", "demo", "T01"], input="")
    assert result.exit_code == 1
    assert f"Restored the previous version of tickets/{FILE_NAME}." in result.output
    assert path.read_text("utf-8") == TICKET
    assert not path.with_name(f".{FILE_NAME}.bak").exists()


def test_edit_interrupted_restores(projects_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = make_ticket(projects_dir)

    def interrupted_editor(command: list[str], file: Path) -> int:
        file.write_text("half-edited", encoding="utf-8")
        raise KeyboardInterrupt

    monkeypatch.setenv("VISUAL", "my-editor")
    monkeypatch.setattr("spoolhq.services.tickets.editor.run_editor", interrupted_editor)
    result = runner.invoke(app, ["tickets", "edit", "demo", "T01"])
    assert result.exit_code == 130  # click's exit code for Ctrl-C
    assert f"Restored the previous version of tickets/{FILE_NAME}." in result.stderr
    assert path.read_bytes() == TICKET.encode()
    assert not path.with_name(f".{FILE_NAME}.bak").exists()


@pytest.mark.integration
def test_edit_warns_about_exit_status_and_done_when(
    projects_dir: Path, fake_editor: Callable[[str], None]
) -> None:
    make_ticket(projects_dir)
    fake_editor("fail")
    failed = runner.invoke(app, ["tickets", "edit", "demo", "T01"])
    assert failed.exit_code == 0, failed.output
    assert "warning: the editor exited with status 3\n" in failed.stderr

    fake_editor("no-done-when")
    result = runner.invoke(app, ["tickets", "edit", "demo", "T01"])
    assert result.exit_code == 0, result.output
    assert f"warning: tickets/{FILE_NAME}: no '## Done when' section\n" in result.stderr


def test_edit_missing_editor(projects_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = make_ticket(projects_dir)
    monkeypatch.setenv("VISUAL", shlex.quote(str(projects_dir / "no-such-editor")))
    result = runner.invoke(app, ["tickets", "edit", "demo", "T01"])
    assert result.exit_code == 1
    assert "error: editor " in result.output
    assert "not found; set $VISUAL or $EDITOR" in result.output
    assert path.read_text("utf-8") == TICKET
    assert not path.with_name(f".{FILE_NAME}.bak").exists()


def test_edit_missing_ticket(projects_dir: Path) -> None:
    make_ticket(projects_dir)
    result = runner.invoke(app, ["tickets", "edit", "demo", "T09"])
    assert result.exit_code == 1
    assert result.output == "error: no ticket T09 in project 'demo'\n"
