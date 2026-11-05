"""services/projects/errors.py: splitting a ``project.yaml`` error into field and message."""

import pytest

from spoolhq.services.projects import split_error


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        (
            "project.yaml: merge_policy.max_diff_lines: must be greater than 0",
            ("merge_policy.max_diff_lines", "must be greater than 0"),
        ),
        ("project.yaml: commands.test: field required", ("commands.test", "field required")),
        ("project.yaml: the file is empty", (None, "the file is empty")),
    ],
)
def test_split_error(line: str, expected: tuple[str | None, str]) -> None:
    assert split_error(line) == expected
