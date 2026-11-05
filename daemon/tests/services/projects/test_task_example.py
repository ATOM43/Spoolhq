"""The example ``project.yaml`` in task.md must validate against the current model."""

import re
from pathlib import Path

from ruamel.yaml import YAML

from spoolhq.services.projects import parse_project

TASK_MD = Path(__file__).parents[4] / "task.md"


def example() -> dict[str, object]:
    text = TASK_MD.read_text(encoding="utf-8")
    match = re.search(r"Example `project\.yaml`:\n\n```yaml\n(.*?)\n```", text, re.DOTALL)
    assert match, "task.md has no example project.yaml"
    data = YAML(typ="safe", pure=True).load(match[1])
    assert isinstance(data, dict)
    return data


def test_task_md_example_project_yaml_validates(git_repo: Path) -> None:
    data = example()
    data["repo"] = str(git_repo)  # the example's ~/code/sim-dashboard doesn't exist here

    project = parse_project(str(data["name"]), data)

    assert project.template is not None
    assert (project.template.name, project.template.source) == ("fastapi-react", "fastapi-react")
    assert project.git.remote == "https://github.com/example/sim-dashboard"
