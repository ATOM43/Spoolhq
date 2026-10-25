"""GitHub: the REST API for pull requests, and the token it needs.

``GitHubClient`` sends the token, the API headers and 30 s timeouts, reports rate
limits with when to retry and redacts the token from every error; ``pulls.py`` creates
and reads pull requests and their reviews; ``token.py`` finds the token (environment,
then the OS keychain). Plain values in and out; this package imports no other service.
See ``docs/github.md``.
"""

from spoolhq.services.github.client import API_URL, API_VERSION, GitHubClient, GitHubError
from spoolhq.services.github.pulls import (
    PullRequest,
    Review,
    ReviewComment,
    create_pull,
    get_pull,
    list_review_comments,
    list_reviews,
)
from spoolhq.services.github.token import MISSING as MISSING_TOKEN
from spoolhq.services.github.token import github_token, store_github_token

__all__ = [
    "API_URL",
    "API_VERSION",
    "MISSING_TOKEN",
    "GitHubClient",
    "GitHubError",
    "PullRequest",
    "Review",
    "ReviewComment",
    "create_pull",
    "get_pull",
    "github_token",
    "list_review_comments",
    "list_reviews",
    "store_github_token",
]
