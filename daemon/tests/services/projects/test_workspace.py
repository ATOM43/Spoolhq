import json
from pathlib import Path
from typing import Any

import pytest

from spoolhq.services.agents import FakeRunner
from spoolhq.services.gates import SHELL_SYNTAX_ERROR as SHELL_SYNTAX
from spoolhq.services.projects import (
    DEFAULT_PROTECTED_PATHS,
    Project,
    ProjectError,
    ProjectValidationError,
    init_project,
    load_project,
    save_project,
    template_description,
)
from spoolhq.services.projects import workspace as workspace_module
from tests.conftest import AGENT_FIXTURES, FakeBackend

KNOWN_BACKENDS = "expected one of: claude-code-cli, codex-cli"


def valid_data(repo: Path) -> dict[str, Any]:
    return {
        "name": "demo",
        "repo": str(repo),
        "default_branch": "main",
        "commands": {"install": "just install", "lint": "just lint", "test": "just test"},
        "agents": {"default": "claude-code-cli", "budget_per_ticket": {"usd": 5, "tokens": 2000}},
        "tracker": {"kind": "clickup", "list_id": "901"},
    }


def write_project(projects_dir: Path, content: dict[str, Any] | str, name: str = "demo") -> Path:
    folder = projects_dir / name
    folder.mkdir(parents=True, exist_ok=True)
    # JSON is valid YAML, so data-driven tests can write dicts directly.
    text = content if isinstance(content, str) else json.dumps(content)
    path = folder / "project.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def set_path(data: dict[str, Any], dotted: str, value: Any) -> None:
    *parents, last = dotted.split(".")
    for part in parents:
        data = data.setdefault(part, {})
    data[last] = value


def del_path(data: dict[str, Any], dotted: str) -> None:
    *parents, last = dotted.split(".")
    for part in parents:
        data = data[part]
    del data[last]


def errors_for(projects_dir: Path, data: dict[str, Any] | str) -> list[str]:
    write_project(projects_dir, data)
    with pytest.raises(ProjectValidationError) as excinfo:
        load_project("demo", projects_dir=projects_dir)
    return excinfo.value.errors


def test_valid_project_loads(projects_dir: Path, git_repo: Path) -> None:
    write_project(projects_dir, valid_data(git_repo))
    project = load_project("demo", projects_dir=projects_dir)
    assert project.repo_path == git_repo
    assert project.limits.gate_retries == 3
    assert project.limits.review_retries == 2
    assert project.merge_policy.max_diff_lines == 400
    assert project.merge_policy.protected() == list(DEFAULT_PROTECTED_PATHS)
    assert project.git.remote is None
    assert project.context.max_chars == 120_000
    assert (project.context.progress_entries, project.context.decisions_lines) == (3, 20)
    assert project.gates.timeouts.model_dump() == {"install": 600, "lint": 300, "test": 900}
    assert project.run.integration == "local"


def test_example_from_task_md_is_valid(projects_dir: Path, git_repo: Path) -> None:
    write_project(
        projects_dir,
        f"""\
name: demo
repo: {json.dumps(str(git_repo))}
default_branch: main
template:
  name: fastapi-react
  source: fastapi-react
  ref: 0.1.0
commands:
  install: just install
  lint: just lint
  test: just test
agents:
  default: claude-code-cli        # claude-code-cli (more backends come later)
  reviewer: claude-code-cli       # optional per-role override
  backends:
    claude-code-cli:
      base_url: http://localhost:11434
      model: qwen3-coder
  budget_per_ticket:
    usd: 5                        # API backends
    tokens: 2000000               # subscription backends
limits:
  gate_retries: 3
  review_retries: 2
merge_policy:
  max_diff_lines: 400
  protected_paths: ["**/migrations/**", ".github/**", "**/auth/**"]
git:
  remote: https://github.com/ATOM43/spoolhq   # optional
tracker:
  kind: clickup                               # optional
  list_id: "901"
""",
    )
    project = load_project("demo", projects_dir=projects_dir)
    assert project.agents.reviewer == "claude-code-cli"
    backend = project.agents.backends["claude-code-cli"]
    assert (backend.base_url, backend.model) == ("http://localhost:11434", "qwen3-coder")
    assert project.agents.budget_per_ticket is not None
    assert project.agents.budget_per_ticket.tokens == 2_000_000
    assert project.template is not None
    assert (project.template.name, project.template.ref) == ("fastapi-react", "0.1.0")


def test_repo_with_tilde_is_expanded(
    projects_dir: Path, git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(git_repo.parent))
    monkeypatch.setenv("USERPROFILE", str(git_repo.parent))
    data = valid_data(git_repo)
    data["repo"] = f"~/{git_repo.name}"
    write_project(projects_dir, data)
    project = load_project("demo", projects_dir=projects_dir)
    assert project.repo == "~/repo"
    assert project.repo_path == git_repo


@pytest.mark.parametrize(
    "field",
    ["name", "repo", "commands.install", "commands.lint", "commands.test", "tracker.list_id"],
)
def test_missing_required_field_is_named(projects_dir: Path, git_repo: Path, field: str) -> None:
    data = valid_data(git_repo)
    del_path(data, field)
    assert errors_for(projects_dir, data) == [f"project.yaml: {field}: field required"]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("git.remote", "https://gitlab.com/owner/repo", "not a GitHub URL"),
        ("git.remote", "http://github.com/owner/repo", "not a GitHub URL"),
        ("git.remote", "https://github.com/owner", "not a GitHub URL"),
        ("git.remote", "https://github.com/owner/repo/tree/main", "not a GitHub URL"),
        ("git.remote", "https://github.com.evil.example/owner/repo", "not a GitHub URL"),
        ("git.remote", "git@github.com:owner/repo", "not a GitHub URL"),
        ("git.remote", "https://github.com/owner/..", "not a GitHub URL"),
        ("git.remote", "https://github.com/-owner/repo", "not a GitHub URL"),
        ("git.remote", "https://github.com/.owner/repo", "not a GitHub URL"),
        ("git.remote", "https://github.com/own_er/repo", "not a GitHub URL"),
        ("git.remote", "https://github.com/own.er/repo", "not a GitHub URL"),
        ("git.remote", "https://github.com/" + "o" * 40 + "/repo", "not a GitHub URL"),
        ("git.remote", "https://github.com/owner/-repo", "not a GitHub URL"),
        ("git.remote", "https://github.com/owner/.repo", "not a GitHub URL"),
        ("git.remote", "https://github.com/owner/re po", "not a GitHub URL"),
        ("git.remote", "https://github.com/owner/re~po", "not a GitHub URL"),
        ("git.remote", "https://github.com/owner/" + "r" * 101, "not a GitHub URL"),
        ("git.remote", "git@github.com:-owner/repo.git", "not a GitHub URL"),
        ("git.remote", "git@github.com:owner/.repo.git", "not a GitHub URL"),
        ("agents.default", "copilot", "unknown backend 'copilot'; " + KNOWN_BACKENDS),
        ("agents.reviewer", "gemini-cli", "unknown backend 'gemini-cli'; " + KNOWN_BACKENDS),
        (
            "agents.backends.claude-code-cli.base_url",
            "http://example.com",
            "'http://example.com': plain http is allowed only for localhost; use https",
        ),
        (
            "agents.backends.claude-code-cli.base_url",
            "https://user:pw@api.example.com",
            "must not contain a username or password",
        ),
        (
            "agents.backends.claude-code-cli.base_url",
            "http://user@localhost:11434",
            "must not contain a username or password",
        ),
        (
            "agents.backends.claude-code-cli.base_url",
            "ftp://localhost",
            "'ftp://localhost' must be an http or https URL",
        ),
        (
            "agents.backends.claude-code-cli.base_url",
            "http://localhost:99999",
            "'http://localhost:99999' is not a valid URL",
        ),
        ("agents.backends.claude-code-cli.model", " ", "must not be empty"),
        ("agents.budget_per_ticket.usd", -1, "must be greater than 0"),
        ("agents.budget_per_ticket.tokens", 0, "must be greater than 0"),
        ("limits.gate_retries", 11, "must be at most 10"),
        ("limits.review_retries", -1, "must be at least 0"),
        ("merge_policy.max_diff_lines", 5, "must be at least 10"),
        ("merge_policy.max_diff_lines", 100_001, "must be at most 100000"),
        ("commands.test", "  ", "must not be empty"),
        ("tracker.kind", "jira", "must be one of 'clickup'"),
        ("run.integration", "github", "must be one of 'local' or 'hold'"),
        ("context.max_chars", 10000, "must be at least 20000"),
        ("context.max_chars", 2_000_001, "must be at most 2000000"),
        ("context.progress_entries", 0, "must be at least 1"),
        ("context.decisions_lines", 10_001, "must be at most 10000"),
        ("gates.timeouts.test", 5, "must be at least 10"),
        ("gates.timeouts.install", 7_201, "must be at most 7200"),
        ("commands.test", "just test && rm -rf /", SHELL_SYNTAX),
        ("commands.test", "just test | tee x", SHELL_SYNTAX),
        ("commands.lint", "echo `id`", SHELL_SYNTAX),
        (
            "commands.install",
            'pip install "x',
            "can't be split into arguments: No closing quotation",
        ),
        ("limits.gate_retires", 3, "unknown key (did you mean 'gate_retries'?)"),
        ("colour", "blue", "unknown key"),
    ],
)
def test_wrong_value_gives_documented_message(
    projects_dir: Path, git_repo: Path, field: str, value: Any, message: str
) -> None:
    data = valid_data(git_repo)
    set_path(data, field, value)
    assert errors_for(projects_dir, data) == [f"project.yaml: {field}: {message}"]


@pytest.mark.parametrize(
    "remote",
    [
        "https://github.com/ATOM43/spoolhq",
        "https://github.com/ATOM43/spoolhq.git",
        "git@github.com:ATOM43/spoolhq.git",
        "https://github.com/some-org/my.repo_name",
        "https://github.com/a/b",
        "https://github.com/Owner-1/_private-repo.v2",
        "https://github.com/" + "o" * 39 + "/" + "r" * 100,
        "git@github.com:" + "o" * 39 + "/" + "r" * 100 + ".git",
    ],
)
def test_github_remotes_are_accepted(projects_dir: Path, git_repo: Path, remote: str) -> None:
    data = valid_data(git_repo)
    set_path(data, "git.remote", remote)
    write_project(projects_dir, data)
    assert load_project("demo", projects_dir=projects_dir).git.remote == remote


def test_registered_backends_are_accepted(
    projects_dir: Path, git_repo: Path, fake_backend: FakeBackend
) -> None:
    fake = fake_backend("fake-a", FakeRunner(AGENT_FIXTURES / "success_writes_file.jsonl"))
    data = valid_data(git_repo)
    data["agents"] = {"default": "claude-code-cli", "planner": "fake-a"}
    write_project(projects_dir, data)
    agents = load_project("demo", projects_dir=projects_dir).agents
    assert agents.backend_for("planner") == "fake-a"
    assert agents.runner_for("planner") is fake
    assert agents.backend_for("implementer") == agents.backend_for("reviewer") == "claude-code-cli"


def test_unknown_backend_in_backends_names_the_field(projects_dir: Path, git_repo: Path) -> None:
    data = valid_data(git_repo)
    data["agents"] = {"backends": {"gemini-cli": {"model": "x"}}}
    [error] = errors_for(projects_dir, data)
    assert error.startswith("project.yaml: agents.backends")
    assert "unknown backend 'gemini-cli'" in error


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:11434",
        "http://127.0.0.1:8080/v1",
        "http://[::1]:11434",
        "https://api.example.com",
    ],
)
def test_good_base_urls_are_accepted(projects_dir: Path, git_repo: Path, url: str) -> None:
    data = valid_data(git_repo)
    data["agents"] = {"backends": {"claude-code-cli": {"base_url": url}}}
    write_project(projects_dir, data)
    agents = load_project("demo", projects_dir=projects_dir).agents
    assert agents.backends["claude-code-cli"].base_url == url


@pytest.mark.parametrize("name", ["../x", "Demo", "-demo", "demo_1", "a" * 64, "", "demo/x"])
def test_bad_slug_is_refused(projects_dir: Path, git_repo: Path, name: str) -> None:
    data = valid_data(git_repo)
    data["name"] = name
    rule = "must be 1-63 lowercase letters, digits or hyphens, starting with a letter or digit"
    assert f"project.yaml: name: {rule}" in errors_for(projects_dir, data)


def test_name_must_match_folder(projects_dir: Path, git_repo: Path) -> None:
    data = valid_data(git_repo)
    data["name"] = "other"
    assert errors_for(projects_dir, data) == [
        "project.yaml: name: 'other' does not match the project folder name 'demo'"
    ]


@pytest.mark.parametrize("revision", ["main~1", "main^", "main@{0}"])
def test_default_branch_must_be_a_branch_name(
    projects_dir: Path, git_repo: Path, revision: str
) -> None:
    data = valid_data(git_repo)
    data["default_branch"] = revision
    assert errors_for(projects_dir, data) == [
        f"project.yaml: default_branch: {revision!r} is not a valid branch name"
    ]


def test_default_branch_main_is_accepted(projects_dir: Path, git_repo: Path) -> None:
    write_project(projects_dir, valid_data(git_repo))
    assert load_project("demo", projects_dir=projects_dir).default_branch == "main"


def test_default_branch_git_error_is_reported(projects_dir: Path, git_repo: Path) -> None:
    # A corrupt packed-refs file makes git fail, which must not read as "not found".
    (git_repo / ".git" / "packed-refs").write_text("not a ref line\n", encoding="utf-8")
    data = valid_data(git_repo)
    data["default_branch"] = "release"
    [error] = errors_for(projects_dir, data)
    assert error.startswith("project.yaml: default_branch: git show-ref failed (exit 128): ")
    assert "packed-refs" in error


def test_all_errors_are_reported_at_once(projects_dir: Path, git_repo: Path) -> None:
    data = valid_data(git_repo)
    del data["commands"]["test"]
    data["limits"] = {"gate_retries": 99}
    data["git"] = {"remote": "nope"}
    assert errors_for(projects_dir, data) == [
        "project.yaml: commands.test: field required",
        "project.yaml: limits.gate_retries: must be at most 10",
        "project.yaml: git.remote: not a GitHub URL",
    ]


def test_list_items_use_index_paths(projects_dir: Path, git_repo: Path) -> None:
    data = valid_data(git_repo)
    data["merge_policy"] = {"protected_paths": ["docs/**", ""]}
    assert errors_for(projects_dir, data) == [
        "project.yaml: merge_policy.protected_paths[1]: must not be empty"
    ]


def test_protected_paths_replace_the_default_and_extra_adds(
    projects_dir: Path, git_repo: Path
) -> None:
    data = valid_data(git_repo)
    data["merge_policy"] = {"protected_paths": ["docs/**"]}
    write_project(projects_dir, data)
    assert load_project("demo", projects_dir=projects_dir).merge_policy.protected() == ["docs/**"]
    data["merge_policy"] = {"protected_paths_extra": ["infra/**"]}
    write_project(projects_dir, data)
    protected = load_project("demo", projects_dir=projects_dir).merge_policy.protected()
    assert protected == [*DEFAULT_PROTECTED_PATHS, "infra/**"]


def test_bad_protected_path_patterns_are_refused(projects_dir: Path, git_repo: Path) -> None:
    data = valid_data(git_repo)
    data["merge_policy"] = {
        "protected_paths": ["/etc/x", "../x"],
        "protected_paths_extra": ["", "C:/x", "a/../b"],
    }
    assert errors_for(projects_dir, data) == [
        "project.yaml: merge_policy.protected_paths[0]: must be a repo-relative pattern, "
        "got '/etc/x'",
        "project.yaml: merge_policy.protected_paths[1]: must not contain '..', got '../x'",
        "project.yaml: merge_policy.protected_paths_extra[0]: must not be empty",
        "project.yaml: merge_policy.protected_paths_extra[1]: must be a repo-relative pattern, "
        "got 'C:/x'",
        "project.yaml: merge_policy.protected_paths_extra[2]: must not contain '..', got 'a/../b'",
    ]


@pytest.mark.parametrize(
    ("repo", "message"),
    [
        ("missing", "path does not exist"),
        ("plain", "not a git work tree"),
        ("relative", "must be an absolute path (or start with ~)"),
    ],
)
def test_bad_repo_in_yaml(
    projects_dir: Path, git_repo: Path, tmp_path: Path, repo: str, message: str
) -> None:
    (tmp_path / "plain").mkdir()
    data = valid_data(git_repo)
    data["repo"] = "some/relative/path" if repo == "relative" else str(tmp_path / repo)
    [error] = errors_for(projects_dir, data)
    assert error.startswith(f"project.yaml: repo: {message}")


def test_missing_branch_in_yaml(projects_dir: Path, git_repo: Path) -> None:
    data = valid_data(git_repo)
    data["default_branch"] = "develop"
    assert errors_for(projects_dir, data) == [
        f"project.yaml: default_branch: branch 'develop' not found in {git_repo}"
    ]


@pytest.mark.parametrize(
    ("text", "location"),
    [
        ("name: demo\ncommands: [a,\n", "line 3, column 1"),
        ("name: demo\n  repo: x\n", "line 2, column 7"),
        ("name: demo\nname: again\n", "line 2, column 1"),
    ],
)
def test_yaml_syntax_error_has_line_and_column(
    projects_dir: Path, text: str, location: str
) -> None:
    write_project(projects_dir, text)
    with pytest.raises(ProjectError) as excinfo:
        load_project("demo", projects_dir=projects_dir)
    assert not isinstance(excinfo.value, ProjectValidationError)
    assert str(excinfo.value).startswith(f"project.yaml: {location}: ")


def test_python_tags_are_not_constructed(projects_dir: Path, git_repo: Path) -> None:
    data = valid_data(git_repo)
    del data["name"]
    text = json.dumps(data)[:-1] + ', "name": !!python/object/apply:os.getcwd []}'
    errors = errors_for(projects_dir, text)
    assert errors == ["project.yaml: name: input should be a valid string"]


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("", "project.yaml: the file is empty"),
        ("- a\n", "project.yaml: expected a mapping of settings"),
    ],
)
def test_empty_or_non_mapping_file(projects_dir: Path, text: str, message: str) -> None:
    assert errors_for(projects_dir, text) == [message]


def test_load_refuses_path_tricks(projects_dir: Path) -> None:
    with pytest.raises(ProjectError, match="invalid project name '../x'"):
        load_project("../x", projects_dir=projects_dir)


def test_load_missing_project(projects_dir: Path) -> None:
    with pytest.raises(ProjectError, match="no project 'nope'"):
        load_project("nope", projects_dir=projects_dir)


def test_load_missing_yaml(projects_dir: Path) -> None:
    (projects_dir / "demo").mkdir(parents=True)
    with pytest.raises(ProjectError, match="project.yaml: not found"):
        load_project("demo", projects_dir=projects_dir)


COMMENTED_YAML = """\
# My project. Keep this comment.
name: demo
repo: {repo}
commands:
  install: just install
  lint: just lint   # runs ruff and eslint
  test: just test
limits:
  gate_retries: 3   # be patient
  review_retries: 2
merge_policy:
  protected_paths: ['**/migrations/**', docs/**]
"""


def test_round_trip_keeps_file_unchanged(projects_dir: Path, git_repo: Path) -> None:
    text = COMMENTED_YAML.format(repo=json.dumps(str(git_repo)))
    path = write_project(projects_dir, text)
    save_project(load_project("demo", projects_dir=projects_dir), projects_dir=projects_dir)
    assert path.read_text(encoding="utf-8") == text


def test_round_trip_change_keeps_comments(projects_dir: Path, git_repo: Path) -> None:
    path = write_project(projects_dir, COMMENTED_YAML.format(repo=json.dumps(str(git_repo))))
    project = load_project("demo", projects_dir=projects_dir)
    limits = project.limits.model_copy(update={"gate_retries": 5})
    save_project(project.model_copy(update={"limits": limits}), projects_dir=projects_dir)

    saved = path.read_text(encoding="utf-8")
    assert "# My project. Keep this comment." in saved
    assert "lint: just lint   # runs ruff and eslint" in saved
    assert "gate_retries: 5" in saved
    assert "# be patient" in saved
    assert "agents" not in saved  # settings the user left out stay out
    assert load_project("demo", projects_dir=projects_dir).limits.gate_retries == 5


def test_save_refuses_invalid_values(projects_dir: Path, git_repo: Path) -> None:
    path = write_project(projects_dir, valid_data(git_repo))
    before = path.read_text(encoding="utf-8")
    project = load_project("demo", projects_dir=projects_dir)
    bad = project.model_copy(
        update={"limits": project.limits.model_copy(update={"gate_retries": 99})}
    )
    with pytest.raises(ProjectValidationError, match="limits.gate_retries: must be at most 10"):
        save_project(bad, projects_dir=projects_dir)
    assert path.read_text(encoding="utf-8") == before


def test_init_creates_workspace(projects_dir: Path, git_repo: Path) -> None:
    result = init_project("demo", git_repo, projects_dir=projects_dir, remote=None)
    folder = projects_dir / "demo"
    assert result.path == folder
    assert sorted(p.name for p in folder.iterdir()) == [
        "CONTEXT.md",
        "project.yaml",
        "runs",
        "tickets",
    ]
    context = (folder / "CONTEXT.md").read_text(encoding="utf-8")
    for heading in ("## Objective", "## Background", "## Requirements", "## Deliverables"):
        assert heading in context
    yaml_text = (folder / "project.yaml").read_text(encoding="utf-8")
    assert "check that these install, lint and test your repo" in yaml_text
    assert "install: just install" in yaml_text
    assert result.missing_notes == ["PROGRESS.md", "DECISIONS.md", "CLAUDE.md"]
    project = load_project("demo", projects_dir=projects_dir)
    assert project == result.project
    assert project.repo_path == git_repo.resolve()


def test_init_with_template_settings(projects_dir: Path, git_repo: Path) -> None:
    commands = {"install": "make deps", "lint": "make lint", "test": "make check"}
    result = init_project(
        "demo",
        git_repo,
        projects_dir=projects_dir,
        commands=commands,
        template={"name": "t", "source": "/srv/t", "ref": None},
        template_description="Made from t.",
    )
    assert result.project.commands.model_dump() == commands
    assert result.project.template is not None
    assert result.project.template.model_dump() == {"name": "t", "source": "/srv/t", "ref": None}
    text = (projects_dir / "demo" / "project.yaml").read_text(encoding="utf-8")
    assert "template:\n  name: t\n  source: /srv/t\n" in text
    assert "ref:" not in text
    assert "From the template's spoolhq-template.yaml." in text
    assert template_description("demo", projects_dir=projects_dir) == "Made from t."
    assert load_project("demo", projects_dir=projects_dir) == result.project


def test_template_description_is_none_without_a_template(
    projects_dir: Path, git_repo: Path
) -> None:
    init_project("demo", git_repo, projects_dir=projects_dir)
    assert template_description("demo", projects_dir=projects_dir) is None


def test_an_unreadable_template_description(projects_dir: Path, git_repo: Path) -> None:
    init_project("demo", git_repo, projects_dir=projects_dir)
    (projects_dir / "demo" / "TEMPLATE.md").write_bytes(b"\xff\xfe bad")
    with pytest.raises(ProjectError, match="cannot read .*TEMPLATE.md"):
        template_description("demo", projects_dir=projects_dir)


def test_a_template_must_be_a_block(projects_dir: Path, git_repo: Path) -> None:
    data = valid_data(git_repo)
    data["template"] = "fastapi-react"
    write_project(projects_dir, json.dumps(data))
    with pytest.raises(ProjectValidationError) as info:
        load_project("demo", projects_dir=projects_dir)
    assert info.value.errors == [
        "project.yaml: template: input should be a valid dictionary or instance of TemplateInfo"
    ]


def test_init_finds_repo_notes(projects_dir: Path, git_repo: Path) -> None:
    for note in ("PROGRESS.md", "DECISIONS.md", "CLAUDE.md"):
        (git_repo / note).write_text("notes\n", encoding="utf-8")
    result = init_project("demo", git_repo, projects_dir=projects_dir)
    assert result.missing_notes == []


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ("missing", "repo: path does not exist"),
        ("plain", "repo: not a git work tree"),
        ("branch", "default_branch: branch 'develop' not found"),
        ("remote", "git.remote: not a GitHub URL"),
        ("name", "name: must be 1-63 lowercase"),
    ],
)
def test_init_refuses_bad_input_and_creates_nothing(
    projects_dir: Path, git_repo: Path, tmp_path: Path, case: str, message: str
) -> None:
    (tmp_path / "plain").mkdir()
    repo = {"missing": tmp_path / "missing", "plain": tmp_path / "plain"}.get(case, git_repo)
    with pytest.raises(ProjectValidationError) as excinfo:
        init_project(
            "../x" if case == "name" else "demo",
            repo,
            projects_dir=projects_dir,
            branch="develop" if case == "branch" else "main",
            remote="https://gitlab.com/a/b" if case == "remote" else None,
        )
    assert any(error.startswith(message) for error in excinfo.value.errors), excinfo.value.errors
    assert not projects_dir.exists()


def test_init_refuses_existing_folder(projects_dir: Path, git_repo: Path) -> None:
    existing = projects_dir / "demo"
    existing.mkdir(parents=True)
    (existing / "keep.txt").write_text("mine", encoding="utf-8")
    with pytest.raises(ProjectError, match="project folder already exists"):
        init_project("demo", git_repo, projects_dir=projects_dir)
    assert [p.name for p in existing.iterdir()] == ["keep.txt"]
    assert [p.name for p in projects_dir.iterdir()] == ["demo"]


def _fail_after_yaml(folder: Path, project: Project, description: str | None) -> None:
    (folder / "project.yaml").write_text("partial", encoding="utf-8")
    raise OSError("disk full")


def test_failure_mid_init_leaves_nothing(
    projects_dir: Path, git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(workspace_module, "_populate", _fail_after_yaml)
    with pytest.raises(OSError, match="disk full"):
        init_project("demo", git_repo, projects_dir=projects_dir)
    assert list(projects_dir.iterdir()) == []


def test_failed_rename_leaves_nothing(
    projects_dir: Path, git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(self: Path, target: Path) -> Path:
        raise OSError("rename failed")

    monkeypatch.setattr(Path, "rename", refuse)
    with pytest.raises(OSError, match="rename failed"):
        init_project("demo", git_repo, projects_dir=projects_dir)
    assert list(projects_dir.iterdir()) == []


def test_init_never_modifies_the_repo(projects_dir: Path, git_repo: Path) -> None:
    before = sorted(p.relative_to(git_repo) for p in git_repo.rglob("*"))
    init_project("demo", git_repo, projects_dir=projects_dir)
    assert sorted(p.relative_to(git_repo) for p in git_repo.rglob("*")) == before


def test_missing_git_is_reported(
    projects_dir: Path, git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("spoolhq.services.git.runner._git_path", None)
    monkeypatch.setattr("spoolhq.services.git.runner.shutil.which", lambda name: None)
    with pytest.raises(ProjectValidationError) as excinfo:
        init_project("demo", git_repo, projects_dir=projects_dir)
    assert excinfo.value.errors == ["repo: git not found on PATH"]
    assert not projects_dir.exists()
