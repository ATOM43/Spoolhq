"""The redactor: named patterns become ``[redacted: <name>]`` in stored text, normal text
is left alone, and the high-entropy values are only those the scan flags by entropy."""

import json
from pathlib import Path

import pytest

from spoolhq.services.gates import (
    FileChange,
    high_entropy_values,
    redact,
    redact_data,
    redact_file,
)
from tests.services.gates.test_secrets import FAKE

ANTHROPIC = FAKE["Anthropic key"] + "Lk2"
RANDOM = "q8Zr2Lx0Vb7Nw4Kp1Ts9Hd3Fy6Jm5Gc0Ua"  # 34 characters, > 4.5 bits


@pytest.mark.parametrize("name", [n for n in FAKE if n != "private key"])
def test_each_named_pattern_is_redacted(name: str) -> None:
    text = f'value = "{FAKE[name]}" # set'
    assert redact(text) == f'value = "[redacted: {name}]" # set'


def test_an_assignment_keeps_its_name_and_quotes() -> None:
    text = "db_password: 'hunter2hunter2hunter2'"
    assert redact(text) == "db_password: '[redacted: secret assignment]'"


def test_a_private_key_body_is_redacted_line_by_line() -> None:
    begin, end = FAKE["private key"], "-----END RSA " + "PRIVATE KEY-----"
    diff = f"+{begin}\n+MIIEvQIBADANBgkqhkiG9w0BAQEF\n+AASCBKcwggSjAgEAAoIBAQC7\n+{end}\n+x = 1\n"
    clean = redact(diff)
    assert "MIIEvQ" not in clean and "AASCBK" not in clean
    assert clean.count("\n") == diff.count("\n")
    assert all(line.startswith("+") for line in clean.splitlines())
    assert clean.endswith("+x = 1\n")


def test_a_key_after_a_json_escape_is_redacted() -> None:
    summary = json.dumps({"content": f"first line\n{ANTHROPIC}\n"})
    assert ANTHROPIC not in redact(summary)
    assert json.loads(redact(summary))["content"] == "first line\n[redacted: Anthropic key]\n"


def test_normal_text_is_untouched() -> None:
    text = (
        "commit 3f786850e387550fdab836ed7e6dc881de23001b\n"
        "id 123e4567-e89b-12d3-a456-426614174000\n"
        "pneumonoultramicroscopicsilicovolcanoconiosis and a sk-short\n"
        'token_path = "~/.spoolhq/token"\n'
    )
    assert redact(text) == text


def test_redact_data_walks_dicts_and_lists() -> None:
    record = {"message": {"content": [{"text": ANTHROPIC, "n": 3}]}, ANTHROPIC: True}
    assert redact_data(record) == {
        "message": {"content": [{"text": "[redacted: Anthropic key]", "n": 3}]},
        "[redacted: Anthropic key]": True,
    }


def test_redact_file_rewrites_only_when_needed(tmp_path: Path) -> None:
    log = tmp_path / "test.log"
    log.write_bytes(b"ok \xff\r\nkey " + ANTHROPIC.encode() + b"\n")
    redact_file(log)
    assert log.read_bytes() == b"ok \xff\r\nkey [redacted: Anthropic key]\n"


def test_high_entropy_values_are_only_those_flagged_by_entropy() -> None:
    change = FileChange(
        "app/config.py",
        None,
        added=(
            (1, f'blob = "{RANDOM}"'),
            (2, f'key = "{ANTHROPIC}" and "{RANDOM[::-1]}"'),  # a named hit wins
            (3, f'ok = "{RANDOM}x"  # spoolhq:allow-secret'),
        ),
    )
    assert high_entropy_values([change], ()) == {RANDOM}
    assert high_entropy_values([change], ("app/**",)) == set()
