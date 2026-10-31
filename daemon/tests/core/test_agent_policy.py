"""The shared environment allowlist for subprocesses (agents, gates, Graphify)."""

from spoolhq.core.agent_policy import allowed_env

PARENT = {
    "PATH": "/usr/bin",
    "HOME": "/home/u",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "TMPDIR": "/var/scratch/u",
    "TEMP": "C:\\Temp",
    "TMP": "C:\\Tmp",
    "SYSTEMROOT": "C:\\Windows",
    "PATHEXT": ".EXE",
    "USERPROFILE": "C:\\Users\\u",
    "LOCALAPPDATA": "C:\\Users\\u\\AppData\\Local",
    "APPDATA": "C:\\Users\\u\\AppData\\Roaming",
    "ANTHROPIC_API_KEY": "sk-secret",
    "GITHUB_TOKEN": "ghp-secret",
    "AWS_SECRET_ACCESS_KEY": "aws-secret",
}


def test_windows_gets_what_processes_need_to_start() -> None:
    env = allowed_env(PARENT, platform="win32")
    for name in ("SYSTEMROOT", "TEMP", "TMP", "PATHEXT", "USERPROFILE", "LOCALAPPDATA"):
        assert env[name] == PARENT[name]
    assert env["APPDATA"] == PARENT["APPDATA"]


def test_windows_names_match_in_any_case() -> None:
    env = allowed_env({"SystemRoot": "C:\\Windows", "Temp": "C:\\T"}, platform="win32")
    assert env == {"SystemRoot": "C:\\Windows", "Temp": "C:\\T"}


def test_secrets_never_pass_on_any_platform() -> None:
    for platform in ("win32", "linux", "darwin"):
        env = allowed_env(PARENT, platform=platform)
        assert not {"ANTHROPIC_API_KEY", "GITHUB_TOKEN", "AWS_SECRET_ACCESS_KEY"} & env.keys()


def test_posix_output_is_unchanged() -> None:
    assert allowed_env(PARENT, platform="linux") == {
        "PATH": "/usr/bin",
        "HOME": "/home/u",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TMPDIR": "/var/scratch/u",
        "TEMP": "C:\\Temp",
        "TMP": "C:\\Tmp",
    }
    assert allowed_env(PARENT, platform="darwin") == allowed_env(PARENT, platform="linux")
