"""Testing a secret against its provider, with a mocked HTTP transport."""

import logging

import httpx
import pytest

from spoolhq.services.secrets import SecretName, store_secret
from spoolhq.services.secrets.check import check_secret

SECRET = "sk-check-0123456789-do-not-leak"  # noqa: S105 - a fake value the test looks for


def answer(status: int) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        # A body and headers that must never reach the result.
        return httpx.Response(status, json={"echo": SECRET}, headers={"x-echo": SECRET})

    return httpx.MockTransport(handler)


def fail(exc: type[httpx.HTTPError]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        raise exc("boom " + SECRET, request=request)

    return httpx.MockTransport(handler)


@pytest.mark.parametrize(
    ("name", "url", "header", "value"),
    [
        ("anthropic", "https://api.anthropic.com/v1/models", "x-api-key", SECRET),
        ("github", "https://api.github.com/user", "authorization", f"Bearer {SECRET}"),
        ("clickup", "https://api.clickup.com/api/v2/user", "authorization", SECRET),
    ],
)
def test_each_provider_gets_one_read_only_call(
    name: SecretName, url: str, header: str, value: str
) -> None:
    store_secret(name, SECRET)
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200)

    result = check_secret(name, transport=httpx.MockTransport(handler))
    assert (result.ok, result.message) == (True, "Key works")
    assert len(seen) == 1
    assert (seen[0].method, str(seen[0].url), seen[0].headers[header]) == ("GET", url, value)
    if name == "anthropic":
        assert seen[0].headers["anthropic-version"] == "2023-06-01"


@pytest.mark.parametrize(
    ("transport", "message"),
    [
        (answer(401), "Rejected (401)"),
        (answer(403), "Rejected (403)"),
        (answer(500), "Unexpected response (500)"),
        (fail(httpx.ReadTimeout), "Timed out"),
        (fail(httpx.ConnectError), "Couldn't reach GitHub"),
    ],
)
def test_failures_map_to_fixed_text(
    transport: httpx.MockTransport, message: str, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    store_secret("github", SECRET)
    result = check_secret("github", transport=transport)
    assert (result.ok, result.message) == (False, message)
    assert SECRET not in caplog.text
    assert all(SECRET not in str(r.__dict__) for r in caplog.records)
    assert [(r.secret, r.outcome) for r in caplog.records if hasattr(r, "outcome")] == [
        ("github", message)
    ]


def test_a_redirect_is_not_followed() -> None:
    store_secret("clickup", SECRET)
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(302, headers={"location": "https://evil.example/steal"})

    result = check_secret("clickup", transport=httpx.MockTransport(handler))
    assert (result.ok, result.message) == (False, "Unexpected response (302)")
    assert calls == ["https://api.clickup.com/api/v2/user"]


def test_not_set_makes_no_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no call without a secret")

    result = check_secret("anthropic", transport=httpx.MockTransport(handler))
    assert (result.ok, result.message) == (False, "Not set")


def test_the_environment_value_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPOOLHQ_CLICKUP_TOKEN", "from-env")
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers["authorization"])
        return httpx.Response(200)

    assert check_secret("clickup", transport=httpx.MockTransport(handler)).ok
    assert seen == ["from-env"]
