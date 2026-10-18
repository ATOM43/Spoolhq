"""No code in services/agents/ may contain the permission-skipping flag or mode.

Only comments and docstrings may mention them; every string, name and attribute in
the code itself is checked.
"""

import ast
from pathlib import Path

import pytest

import spoolhq.services.agents

AGENTS_DIR = Path(spoolhq.services.agents.__file__).parent
FORBIDDEN = ("dangerously-skip-permissions", "bypassPermissions")


def docstrings(tree: ast.Module) -> set[int]:
    """ids of the string constants that are docstrings."""
    found: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                found.add(id(body[0].value))
    return found


def offending(source: str) -> list[str]:
    tree = ast.parse(source)
    skip = docstrings(tree)
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            text = node.value
        elif isinstance(node, ast.Name):
            text = node.id
        elif isinstance(node, ast.Attribute):
            text = node.attr
        else:
            continue
        hits += [word for word in FORBIDDEN if word in text]
    return hits


@pytest.mark.parametrize("path", sorted(AGENTS_DIR.glob("*.py")), ids=lambda p: p.name)
def test_no_skip_permissions_in_agents_code(path: Path) -> None:
    assert offending(path.read_text(encoding="utf-8")) == []


def test_the_check_finds_them() -> None:
    assert offending('ARGS = ["--dangerously-skip-permissions"]') == [
        "dangerously-skip-permissions"
    ]
    assert offending('mode = f"{x}bypassPermissions"') == ["bypassPermissions"]
    assert offending('"""Never bypassPermissions."""\n# bypassPermissions\nx = 1') == []
