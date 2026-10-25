"""`spool secrets set github` and `spool github sync`.

The token is read from a hidden prompt, never from argv, and stored in the OS keychain;
`SPOOLHQ_GITHUB_TOKEN` in the daemon's environment wins over it. `github sync` asks
the daemon to check the project's open pull requests now.
"""

import getpass
from typing import Annotated

import typer
from keyring.errors import KeyringError

from spoolhq.cli.client import ApiClient, ApiError
from spoolhq.cli.common import fail, settings
from spoolhq.services.github import store_github_token

secrets_app = typer.Typer(
    name="secrets", help="Store secrets in the OS keychain.", no_args_is_help=True
)
github_app = typer.Typer(name="github", help="GitHub pull requests.", no_args_is_help=True)

# Fetching and pushing for every open pull request can take a while.
SYNC_TIMEOUT_S = 300.0


def _client() -> ApiClient:
    return ApiClient.from_settings(settings(), timeout=SYNC_TIMEOUT_S)


@secrets_app.command("set")
def set_command(
    name: Annotated[str, typer.Argument(metavar="NAME", help="The secret to set: github.")],
) -> None:
    """Store a secret, read from a hidden prompt (never from the command line)."""
    if name != "github":
        fail(f"error: unknown secret {name!r}; the only one is github")
    token = getpass.getpass("GitHub token (input hidden): ")
    try:
        store_github_token(token)
    except ValueError as exc:
        fail(f"error: {exc}")
    except (KeyringError, RuntimeError) as exc:
        fail(
            f"error: cannot write to the OS keychain ({type(exc).__name__}); "
            "set SPOOLHQ_GITHUB_TOKEN in the daemon's environment instead"
        )
    typer.echo("Stored the GitHub token in the OS keychain (service spoolhq, key github).")


@github_app.command("sync")
def sync_command(project: Annotated[str, typer.Argument(help="Project name.")]) -> None:
    """Check the project's open pull requests now (the daemon also does it every 60 s)."""
    try:
        with _client() as client:
            lines = client.post(f"/api/projects/{project}/github/sync")["lines"]
    except ApiError as exc:
        fail(f"error: {exc}")
    for line in lines:
        typer.echo(line)
    if not lines:
        typer.echo(f"no open pull requests in '{project}'")
