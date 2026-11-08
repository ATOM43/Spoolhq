import sys
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


def test_serve_has_no_port_option() -> None:
    # The desktop app and the CLI find the daemon through SPOOLHQ_PORT / config.toml only.
    result = runner.invoke(app, ["serve", "--help"])
    assert result.exit_code == 0
    assert "--port" not in result.output


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


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, text="<!doctype html><title>Some other app</title>"),
        httpx.Response(200, json={"name": "another service"}),
    ],
)
def test_client_reports_a_server_that_is_not_spoolhq(response: httpx.Response) -> None:
    transport = httpx.MockTransport(lambda request: response)
    with ApiClient("http://127.0.0.1:8765", "abc", transport=transport) as client:
        with pytest.raises(ApiError) as raised:
            client.version()
    assert str(raised.value) == "not a SpoolHQ daemon at http://127.0.0.1:8765"


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


@pytest.mark.parametrize(("scenario", "frozen"), [("happy", True), ("nope", False)])
def test_serve_refuses_the_fake_runner_frozen_or_unknown(
    monkeypatch: pytest.MonkeyPatch, home: Path, scenario: str, frozen: bool
) -> None:
    monkeypatch.setenv("SPOOLHQ_DEV_FAKE_RUNNER", scenario)
    if frozen:
        monkeypatch.setattr("sys.frozen", True, raising=False)
    result = runner.invoke(app, ["serve"])
    assert result.exit_code == 1
    assert "error: SPOOLHQ_DEV_FAKE_RUNNER is for development only" in result.output
    assert not home.exists()  # refused before anything starts


def test_serve_logs_the_fake_runner_and_passes_its_agents(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    from spoolhq.services.agents import FakeRunner

    main = sys.modules["spoolhq.cli.main"]  # ``spoolhq.cli.main`` is also a function

    monkeypatch.setenv("SPOOLHQ_DEV_FAKE_RUNNER", "gate-retry")
    built: dict[str, object] = {}

    def fake_create_app(settings: object, **kwargs: object) -> object:
        built.update(kwargs)
        raise SystemExit(0)  # stop before uvicorn starts

    monkeypatch.setattr(main, "create_app", fake_create_app)
    monkeypatch.setattr(main, "configure_logging", lambda *a, **k: Path("daemon.log"))
    with caplog.at_level("WARNING", logger="spoolhq"):
        result = runner.invoke(app, ["serve"])
    assert result.exit_code == 0, result.output
    assert built["fake_runner"] == "gate-retry"
    assert isinstance(built["agents"].implementer, FakeRunner)  # type: ignore[attr-defined]
    assert "Fake runner active: gate-retry" in caplog.messages
