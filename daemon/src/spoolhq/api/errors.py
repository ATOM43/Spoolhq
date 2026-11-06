"""One error format for every non-2xx answer:
``{"error": {"code": "<snake_case>", "message": "<readable>", "field": "<optional>"}}``.

Routers raise ``ApiError`` (or wrap service calls in ``service_errors``); FastAPI's own
404/405 and validation errors are rewritten by the handlers ``install`` adds. Messages
never echo request values, since those can be secrets or untrusted ticket text.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from spoolhq.services.planner import PlanInvalid
from spoolhq.services.projects import ProjectError, ProjectValidationError
from spoolhq.services.runloop import RunLoopError
from spoolhq.services.scheduler import PlanProblem, SchedulerError
from spoolhq.services.tickets import TicketError, TicketValidationError

STATUS_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "payload_too_large",
    422: "validation_error",
}
RUN_LOOP_STATUS = {"not_found": status.HTTP_404_NOT_FOUND}


class ErrorBody(BaseModel):
    code: str
    message: str
    field: str | None = None
    etag: str | None = None
    """412 ``edit_conflict``: the file's current ETag."""
    current: Any = None
    """412 ``edit_conflict``: the file's current content, as its GET returns it."""
    problems: list[dict[str, Any]] | None = None
    """409 ``plan_invalid``: every problem, as ``GET …/plan`` lists them."""


class ErrorResponse(BaseModel):
    error: ErrorBody


class ApiError(Exception):
    def __init__(
        self, status_code: int, code: str, message: str, *, field: str | None = None, **extra: Any
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = ErrorBody(code=code, message=message, field=field, **extra)


def error_response(
    status_code: int, code: str, message: str, headers: dict[str, str] | None = None
) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message))
    return JSONResponse(body.model_dump(exclude_none=True), status_code, headers=headers)


def problem_view(problem: PlanProblem) -> dict[str, Any]:
    return {"code": problem.code, "message": problem.message, "ticket_ids": problem.ticket_ids}


@contextmanager
def service_errors() -> Iterator[None]:
    """Refusals from the services become ApiErrors: unknown things 404, the rest 409
    (or 422 for invalid content), with the service's message."""
    try:
        yield
    except PlanInvalid as exc:
        problems = [problem_view(problem) for problem in exc.problems]
        raise ApiError(409, "plan_invalid", str(exc), problems=problems) from exc
    except RunLoopError as exc:
        raise ApiError(RUN_LOOP_STATUS.get(exc.code, 409), exc.code, str(exc)) from exc
    except (ProjectValidationError, TicketValidationError) as exc:
        raise ApiError(422, "validation_error", "\n".join(exc.errors)) from exc
    except (ProjectError, TicketError) as exc:
        # shortcut: "no project …"/"no ticket …" is how both services say "unknown";
        # give them a NotFound error class if a message ever changes.
        code = 404 if str(exc).startswith("no ") else 409
        raise ApiError(code, STATUS_CODES[code], str(exc)) from exc
    except SchedulerError as exc:
        raise ApiError(409, "invalid_transition", str(exc)) from exc


async def _api_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApiError)  # noqa: S101 - registered for ApiError only
    body = ErrorResponse(error=exc.body).model_dump(exclude_none=True)
    return JSONResponse(body, exc.status_code)


async def _http_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, HTTPException)  # noqa: S101 - registered for HTTPException only
    code = STATUS_CODES.get(exc.status_code, f"http_{exc.status_code}")
    return error_response(exc.status_code, code, str(exc.detail), dict(exc.headers or {}))


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)  # noqa: S101 - registered for it only
    first = exc.errors()[0] if exc.errors() else {}
    loc = [str(part) for part in first.get("loc", ())]
    field = ".".join(loc[1:]) or None
    message = f"{field}: {first.get('msg', 'invalid')}" if field else str(first.get("msg"))
    body = ErrorResponse(error=ErrorBody(code="validation_error", message=message, field=field))
    return JSONResponse(body.model_dump(exclude_none=True), 422)


def install(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error)
    app.add_exception_handler(HTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
