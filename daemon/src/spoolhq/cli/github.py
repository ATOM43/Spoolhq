"""`spool secrets set github|anthropic|endpoint:<backend>` and `spool github sync`.

A token is read from a hidden prompt, never from argv, and stored in the OS keychain;
`SPOOLHQ_GITHUB_TOKEN` (or `ANTHROPIC_API_KEY`, `SPOOLHQ_ENDPOINT_TOKEN_<BACKEND>`) in the
daemon's environment wins over it. `github sync` asks
the daemon to check the project's open pull requests now.
"""

import getpass
from collections.abc import Callable
from functools import partial
from typing import Annotated

import typer
from keyring.errors import KeyringError

from spoolhq.cli.client import ApiClient, ApiError
from spoolhq.cli.common import fail, settings
from spoolhq.services.agents import backend_names
from spoolhq.services.agents.agent_sdk import store_api_key
from spoolhq.services.agents.endpoint import keyring_key, store_endpoint_token, token_var
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
    name: Annotated[
        str,
        typer.Argument(
            metavar="NAME", help="The secret to set: github, anthropic or endpoint:<backend>."
        ),
    ],
) -> None:
    """Store a secret, read from a hidden prompt (never from the command line)."""
    endpoints = {keyring_key(backend): backend for backend in backend_names()}
    store: Callable[[str], None]
    if name == "github":
        label, key, env_var = "GitHub token", "github", "SPOOLHQ_GITHUB_TOKEN"
        store = store_github_token
    elif name == "anthropic":
        label, key, env_var = "Anthropic API key", "anthropic", "ANTHROPIC_API_KEY"
        store = store_api_key
    elif name in endpoints:
        backend = endpoints[name]
        label, key, env_var = f"token for {backend}'s custom endpoint", name, token_var(backend)
        store = partial(store_endpoint_token, backend)
    else:
        known = ", ".join(["github", "anthropic", *endpoints])
        fail(f"error: unknown secret {name!r}; expected one of: {known}")
    token = getpass.getpass(f"{label[0].upper()}{label[1:]} (input hidden): ")
    try:
        store(token)
    except ValueError as exc:
        fail(f"error: {exc}")
    except (KeyringError, RuntimeError) as exc:
        fail(
            f"error: cannot write to the OS keychain ({type(exc).__name__}); "
            f"set {env_var} in the daemon's environment instead"
        )
    typer.echo(f"Stored the {label} in the OS keychain (service spoolhq, key {key}).")


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
