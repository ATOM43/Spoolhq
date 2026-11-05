"""Daemon settings and secrets (token required). A secret's value is write-only: it goes
to the OS keychain and is never echoed, logged or written to a file."""

from fastapi import APIRouter, Request, Security, status
from keyring.errors import KeyringError

from spoolhq.api.errors import ApiError
from spoolhq.api.params import settings
from spoolhq.api.schemas.settings import DaemonSettings, SecretTest, SecretValue, SecretView
from spoolhq.api.security import bearer_scheme
from spoolhq.services.secrets import (
    SECRETS,
    SecretName,
    delete_secret,
    secret_status,
    store_secret,
)
from spoolhq.services.secrets.check import check_secret

router = APIRouter(prefix="/api/settings", dependencies=[Security(bearer_scheme)])


@router.get("")
def get_settings(request: Request) -> DaemonSettings:
    current = settings(request)
    secrets: dict[str, SecretView] = {}
    for name in SECRETS:
        found = secret_status(name)
        secrets[name] = SecretView(set=found.set, source=found.source)
    return DaemonSettings(
        host=current.host,
        port=current.port,
        log_level=current.log_level,
        projects_dir=str(current.projects_dir),
        worktrees_dir=str(current.worktrees_dir),
        allowed_origins=current.allowed_origins,
        secrets=secrets,
    )


def _keychain_error(exc: Exception) -> ApiError:
    # Only the exception's type: its text could quote what was stored.
    return ApiError(
        409, "keychain_unavailable", f"cannot use the OS keychain ({type(exc).__name__})"
    )


@router.put("/secrets/{secret}", status_code=status.HTTP_204_NO_CONTENT)
def put_secret(secret: SecretName, body: SecretValue) -> None:
    try:
        store_secret(secret, body.value)
    except ValueError as exc:
        raise ApiError(422, "validation_error", "the value is empty", field="value") from exc
    except (KeyringError, RuntimeError) as exc:
        raise _keychain_error(exc) from None


@router.delete("/secrets/{secret}", status_code=status.HTTP_204_NO_CONTENT)
def delete_secret_route(secret: SecretName) -> None:
    try:
        delete_secret(secret)
    except (KeyringError, RuntimeError) as exc:
        raise _keychain_error(exc) from None


@router.post("/secrets/{secret}/test")
def check_secret_route(secret: SecretName) -> SecretTest:
    """One read-only call to the provider with the stored secret; the value stays here."""
    result = check_secret(secret)
    return SecretTest(ok=result.ok, message=result.message)
