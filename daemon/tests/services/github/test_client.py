"""services/github/client.py: headers, token redaction, errors and rate limits."""

from datetime import UTC, datetime

import httpx
import pytest

from spoolhq.services.github import API_VERSION, GitHubClient, GitHubError

TOKEN = "ghp_secret0123456789abcdef"  # noqa: S105 - a fake token
NOW = datetime(2026, 10, 25, 9, 0, tzinfo=UTC)


def client(handler: httpx.MockTransport) -> GitHubClient:
    return GitHubClient(TOKEN, transport=handler, clock=lambda: NOW)


def test_requests_carry_the_token_and_api_headers() -> None:
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    with client(httpx.MockTransport(handle)) as github:
        assert github.request("GET", "/repos/acme/demo") == {"ok": True}
    request = seen[0]
    assert str(request.url) == "https://api.github.com/repos/acme/demo"
    assert request.headers["Authorization"] == f"Bearer {TOKEN}"
    assert request.headers["Accept"] == "application/vnd.github+json"
    assert request.headers["X-GitHub-Api-Version"] == API_VERSION
    assert github._http.timeout.read == 30.0


def test_an_empty_answer_is_none() -> None:
    handler = httpx.MockTransport(lambda _: httpx.Response(204))
    assert client(handler).request("DELETE", "/x") is None


def test_an_error_names_the_call_and_redacts_the_token() -> None:
    body = {"message": f"Bad credentials for {TOKEN}", "errors": [{"code": "invalid"}]}
    handler = httpx.MockTransport(lambda _: httpx.Response(422, json=body))
    with pytest.raises(GitHubError) as caught:
        client(handler).request("POST", "/repos/acme/demo/pulls")
    message = str(caught.value)
    assert message.startswith("GitHub API POST /repos/acme/demo/pulls: HTTP 422: Bad credentials")
    assert TOKEN not in message and "[redacted]" in message
    assert caught.value.status == 422 and caught.value.retry_at is None


def test_a_non_json_error_and_a_network_error() -> None:
    handler = httpx.MockTransport(lambda _: httpx.Response(502, text="Bad gateway"))
    with pytest.raises(GitHubError, match="HTTP 502: Bad gateway"):
        client(handler).request("GET", "/x")

    def broken(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"cannot connect with {TOKEN}", request=request)

    with pytest.raises(GitHubError) as caught:
        client(httpx.MockTransport(broken)).request("GET", "/x")
    assert "ConnectError" in str(caught.value) and TOKEN not in str(caught.value)
    assert caught.value.__cause__ is None and caught.value.__suppress_context__


@pytest.mark.parametrize(
    ("status", "headers", "expected"),
    [
        (429, {"Retry-After": "120"}, datetime(2026, 10, 25, 9, 2, tzinfo=UTC)),
        (403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1792918800"}, None),
        (403, {"X-RateLimit-Remaining": "0"}, datetime(2026, 10, 25, 9, 1, tzinfo=UTC)),
        (429, {}, datetime(2026, 10, 25, 9, 1, tzinfo=UTC)),
    ],
)
def test_rate_limits_say_when_to_retry(
    status: int, headers: dict[str, str], expected: datetime | None
) -> None:
    handler = httpx.MockTransport(lambda _: httpx.Response(status, headers=headers, json={}))
    with pytest.raises(GitHubError, match="rate limited") as caught:
        client(handler).request("GET", "/x")
    assert caught.value.retry_at == (expected or datetime.fromtimestamp(1792918800, UTC))


def test_a_plain_403_is_not_a_rate_limit() -> None:
    handler = httpx.MockTransport(lambda _: httpx.Response(403, json={"message": "Forbidden"}))
    with pytest.raises(GitHubError, match="HTTP 403: Forbidden") as caught:
        client(handler).request("GET", "/x")
    assert caught.value.retry_at is None
