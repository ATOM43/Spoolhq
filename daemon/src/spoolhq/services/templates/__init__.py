"""Templates: project skeletons that ``spool init --template`` generates a repo from.

A template is a Copier template with a ``spoolhq-template.yaml`` contract (name,
description for the planner, install/lint/test commands). Sources are built-in names
(package data under ``spoolhq/templates/``), local folders or git URLs. Templates get
no trust: Copier tasks, migrations and Jinja extensions are refused. ``check_template``
generates one into a temp folder and runs its gates. This package may import
``services.projects``, ``services.gates`` and ``services.git``. See ``docs/templates.md``.
"""

from spoolhq.services.templates.check import CheckResult, check_template
from spoolhq.services.templates.contract import (
    CONTRACT_FILE,
    MAX_DESCRIPTION,
    TemplateCommands,
    TemplateContract,
    TemplateError,
    load_contract,
    parse_contract,
)
from spoolhq.services.templates.generate import (
    check_safe,
    check_target,
    init_from_template,
    init_repo,
    render,
    unsafe_message,
)
from spoolhq.services.templates.sources import (
    ResolvedTemplate,
    builtin_descriptions,
    builtin_names,
    builtin_root,
    is_git_url,
    open_template,
)

__all__ = [
    "CONTRACT_FILE",
    "MAX_DESCRIPTION",
    "CheckResult",
    "ResolvedTemplate",
    "TemplateCommands",
    "TemplateContract",
    "TemplateError",
    "builtin_descriptions",
    "builtin_names",
    "builtin_root",
    "check_safe",
    "check_target",
    "check_template",
    "init_from_template",
    "init_repo",
    "is_git_url",
    "load_contract",
    "open_template",
    "parse_contract",
    "render",
    "unsafe_message",
]
