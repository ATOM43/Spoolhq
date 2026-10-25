"""services/github/pulls.py: creating and reading pull requests and their reviews."""

import json

import httpx
import pytest

from spoolhq.services.github import (
    GitHubClient,
    GitHubError,
    create_pull,
    get_pull,
    list_review_comments,
    list_reviews,
)

PULL = {
    "number": 7,
    "html_url": "https://github.com/acme/demo/pull/7",
    "state": "closed",
    "merged": True,
    "merge_commit_sha": "a" * 40,
    "head": {"sha": "b" * 40, "ref": "spoolhq/T01-x"},
}


def github(routes: dict[tuple[str, str], object], seen: list[httpx.Request]) -> GitHubClient:
    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=routes[(request.method, request.url.path)])

    return GitHubClient("t", transport=httpx.MockTransport(handle))


def test_create_and_get() -> None:
    seen: list[httpx.Request] = []
    client = github(
        {("POST", "/repos/acme/demo/pulls"): PULL, ("GET", "/repos/acme/demo/pulls/7"): PULL},
        seen,
    )
    pr = create_pull(client, "acme/demo", head="spoolhq/T01-x", base="main", title="T", body="B")
    assert json.loads(seen[0].content) == {
        "title": "T",
        "head": "spoolhq/T01-x",
        "base": "main",
        "body": "B",
    }
    assert (pr.number, pr.url, pr.state, pr.merged) == (7, PULL["html_url"], "closed", True)
    assert (pr.merge_commit_sha, pr.head_sha) == ("a" * 40, "b" * 40)
    assert get_pull(client, "acme/demo", 7) == pr


def test_unexpected_pull_data() -> None:
    client = github({("GET", "/repos/acme/demo/pulls/7"): {"number": 7}}, [])
    with pytest.raises(GitHubError, match="unexpected pull request data"):
        get_pull(client, "acme/demo", 7)


def test_reviews_and_comments() -> None:
    seen: list[httpx.Request] = []
    reviews = [
        {
            "id": 1,
            "state": "CHANGES_REQUESTED",
            "body": None,
            "user": {"login": "ann"},
            "submitted_at": "2026-10-25T09:00:00Z",
        },
        "junk",
    ]
    comments = [{"pull_request_review_id": 1, "path": "a.py", "line": 3, "body": "rename"}]
    client = github(
        {
            ("GET", "/repos/acme/demo/pulls/7/reviews"): reviews,
            ("GET", "/repos/acme/demo/pulls/7/comments"): comments,
        },
        seen,
    )
    [review] = list_reviews(client, "acme/demo", 7)
    assert (review.id, review.state, review.body, review.author) == (
        1,
        "CHANGES_REQUESTED",
        "",
        "ann",
    )
    [comment] = list_review_comments(client, "acme/demo", 7)
    assert (comment.review_id, comment.path, comment.line, comment.body) == (1, "a.py", 3, "rename")
    assert seen[0].url.params["per_page"] == "100"


def test_a_non_list_answer_is_no_reviews() -> None:
    client = github({("GET", "/repos/acme/demo/pulls/7/reviews"): {"message": "?"}}, [])
    assert list_reviews(client, "acme/demo", 7) == []
