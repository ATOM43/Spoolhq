from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

import spoolhq
from spoolhq.cli import app
from spoolhq.cli.client import ApiClient, ApiError, DaemonNotRunning

runner = CliRunner()


def test_version_without_daemon(monkeypatch: pytest.MonkeyPatch, free_port: int) -> None:
    monkeypatch.setenv("SPOOLHQ_PORT", str(free_port))
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0, result.output
    assert f"spool {spoolhq.__version__}" in result.output
    assert "daemon not running (start it with `spool serve`)" in result.output


def test_version_with_bad_config_fails_readably(home: Path) -> None:
    home.mkdir()
    (home / "config.toml").write_text('port = "x"\n', encoding="utf-8")
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 1
    assert "invalid setting 'port'" in result.output
    assert "Traceback" not in result.output


def test_serve_refuses_non_loopback_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPOOLHQ_HOST", "0.0.0.0")  # noqa: S104 - the value under test
    result = runner.invoke(app, ["serve"])
    assert result.exit_code == 1
    assert "only listens on 127.0.0.1" in result.output


def test_client_connection_refused(free_port: int) -> None:
    with (
        ApiClient(f"http://127.0.0.1:{free_port}", "token") as client,
        pytest.raises(DaemonNotRunning),
    ):
        client.version()


def test_client_sends_token_and_reports_401() -> None:
    seen: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("Authorization"))
        return httpx.Response(401, json={"detail": "missing or invalid token"})

    transport = httpx.MockTransport(handler)
    with ApiClient("http://127.0.0.1:8765", "abc", transport=transport) as client:
        with pytest.raises(ApiError, match="rejected the token"):
            client.version()
    assert seen == ["Bearer abc"]
