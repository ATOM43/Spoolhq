"""Pull requests: create, read, and list their reviews and review comments.

``repo`` is ``owner/repo`` as ``services.git.github_repo`` reads it from ``git.remote``
(validated, so it is safe in a URL path). Everything GitHub returns is untrusted text.
"""

from dataclasses import dataclass
from typing import Any

from spoolhq.services.github.client import GitHubClient, GitHubError

PER_PAGE = 100


@dataclass(frozen=True)
class PullRequest:
    number: int
    url: str
    """The PR's page on github.com (``html_url``)."""
    state: str
    """``open`` or ``closed``."""
    merged: bool
    merge_commit_sha: str | None
    head_sha: str


@dataclass(frozen=True)
class Review:
    id: int
    state: str
    """``APPROVED``, ``CHANGES_REQUESTED``, ``COMMENTED``, ``DISMISSED`` or ``PENDING``."""
    body: str
    author: str
    submitted_at: str | None
    """ISO 8601 in UTC, as GitHub gives it (``2026-10-25T09:00:00Z``)."""


@dataclass(frozen=True)
class ReviewComment:
    review_id: int | None
    path: str
    line: int | None
    body: str


def _pull(data: Any) -> PullRequest:
    try:
        return PullRequest(
            number=int(data["number"]),
            url=str(data["html_url"]),
            state=str(data["state"]),
            merged=bool(data.get("merged") or data.get("merged_at")),
            merge_commit_sha=data.get("merge_commit_sha"),
            head_sha=str(data["head"]["sha"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise GitHubError(f"unexpected pull request data from GitHub: {exc!r}") from None


def create_pull(
    client: GitHubClient, repo: str, *, head: str, base: str, title: str, body: str
) -> PullRequest:
    data = {"title": title, "head": head, "base": base, "body": body}
    return _pull(client.request("POST", f"/repos/{repo}/pulls", json=data))


def get_pull(client: GitHubClient, repo: str, number: int) -> PullRequest:
    return _pull(client.request("GET", f"/repos/{repo}/pulls/{number}"))


def _list(client: GitHubClient, path: str) -> list[dict[str, Any]]:
    # shortcut: the first 100 only; a PR with more reviews or comments loses the newest.
    data = client.request("GET", path, params={"per_page": PER_PAGE})
    return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []


def list_reviews(client: GitHubClient, repo: str, number: int) -> list[Review]:
    return [
        Review(
            id=int(item.get("id", 0)),
            state=str(item.get("state", "")),
            body=str(item.get("body") or ""),
            author=str((item.get("user") or {}).get("login", "")),
            submitted_at=item.get("submitted_at"),
        )
        for item in _list(client, f"/repos/{repo}/pulls/{number}/reviews")
    ]


def list_review_comments(client: GitHubClient, repo: str, number: int) -> list[ReviewComment]:
    return [
        ReviewComment(
            review_id=item.get("pull_request_review_id"),
            path=str(item.get("path", "")),
            line=item.get("line"),
            body=str(item.get("body") or ""),
        )
        for item in _list(client, f"/repos/{repo}/pulls/{number}/comments")
    ]
