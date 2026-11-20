"""The secret scan: each pattern on an added line fails with path, line and pattern
name, never the value; removed lines, lockfiles (for entropy) and allowed lines pass."""

import random
import string

import pytest

from spoolhq.services.gates import FileChange, GateStatus, scan_secrets
from spoolhq.services.gates.secrets import entropy

# Built from parts so this file carries no literal secret of its own.
FAKE = {
    "private key": "-----BEGIN RSA " + "PRIVATE KEY-----",
    "AWS access key id": "AKIA" + "Q3EXAMPLE7ABCDEF",
    "GitHub token": "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8",
    "Anthropic key": "sk-ant-" + "api03-Zx9Yw8Vu7Ts6Rq5Po4Nm3",
    "OpenAI-style key": "sk-" + "proj-Ab12Cd34Ef56Gh78Ij90",
    "Slack token": "xoxb-" + "1234567890-abcdefghij",
}


def lines(path: str, *texts: str) -> FileChange:
    return FileChange(path, None, added=tuple(enumerate(texts, start=1)))


def scan(*changes: FileChange, allow: tuple[str, ...] = ()) -> tuple[GateStatus, str]:
    result = scan_secrets(changes, allow)
    return result.status, result.excerpt


@pytest.mark.parametrize("name", list(FAKE))
def test_each_pattern_is_caught_on_an_added_line(name: str) -> None:
    value = FAKE[name]
    status, text = scan(lines("app/config.py", "x = 1", f'value = "{value}"'))
    assert status is GateStatus.FAILED
    assert text == f"Possible secret in app/config.py:2 ({name})"
    assert value not in text


@pytest.mark.parametrize("name", list(FAKE))
def test_a_removed_line_is_never_scanned(name: str) -> None:
    removed = FileChange("app/config.py", f'value = "{FAKE[name]}"\n'.encode())
    assert scan(removed) == (GateStatus.PASSED, "")


def test_an_assignment_to_a_secret_name_is_caught() -> None:
    value = "hunter2hunter2hunter2"
    status, text = scan(lines("settings.yml", f'db_password: "{value}"'))
    assert (status, text) == (
        GateStatus.FAILED,
        "Possible secret in settings.yml:1 (secret assignment)",
    )
    paths = lines("a.py", 'token_path = "~/.spoolhq/token-file"', 'API_KEY = "${{ secrets.KEY }}"')
    assert scan(paths)[0] is GateStatus.PASSED


def random_string(size: int) -> str:
    chars = random.Random(7).choices(  # noqa: S311 - a fixed test string
        string.ascii_letters + string.digits, k=size
    )
    return "".join(chars)


def test_a_high_entropy_string_is_caught_but_not_in_a_lockfile() -> None:
    value = random_string(40)
    assert entropy(value) > 4.5
    status, text = scan(lines("src/x.ts", f'const v = "{value}";'))
    assert (status, text) == (
        GateStatus.FAILED,
        "Possible secret in src/x.ts:1 (high-entropy string)",
    )
    assert scan(lines("web/pnpm-lock.yaml", f"  integrity: '{value}'"))[0] is GateStatus.PASSED
    assert scan(lines("a.py", f'x = "{"ab" * 20}"'))[0] is GateStatus.PASSED


def test_the_allow_comment_and_allowed_paths_pass() -> None:
    value = FAKE["GitHub token"]
    commented = lines("a.py", f'TOKEN = "{value}"  # spoolhq:allow-secret')
    assert scan(commented)[0] is GateStatus.PASSED
    fixture = lines("tests/fixtures/keys.py", f'TOKEN = "{value}"')
    assert scan(fixture, allow=("tests/fixtures/**",))[0] is GateStatus.PASSED
    assert scan(fixture)[0] is GateStatus.FAILED


def test_a_long_line_scans_in_linear_time() -> None:
    long = "a" * 200_000 + "=" + "'" * 50_000
    assert scan(lines("min.js", long))[0] is GateStatus.PASSED
