"""The Agent SDK run's helpers that need no process."""

import pytest

from spoolhq.services.agents.agent_sdk_stream import billing_error


@pytest.mark.parametrize(
    ("message", "found"),
    [
        ({"type": "assistant", "error": "billing_error"}, "billing_error"),
        ({"type": "assistant", "error": "rate_limit"}, None),
        ({"type": "system", "subtype": "api_retry", "error": "billing_error"}, "billing_error"),
        ({"type": "system", "subtype": "api_retry", "error": "overloaded"}, None),
        (
            {"type": "result", "is_error": True, "errors": ["Credit balance is too low"]},
            "Credit balance is too low",
        ),
        ({"type": "result", "is_error": True, "result": "Prompt is too long"}, None),
        ({"type": "result", "is_error": False, "result": "fixed the billing module"}, None),
        ({"type": "user"}, None),
    ],
)
def test_billing_errors_are_recognised(message: dict[str, object], found: str | None) -> None:
    assert billing_error(message) == found
