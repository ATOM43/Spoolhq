"""``generate_plan()``: one read-only agent run that turns a project's spec into drafts.

The agent runs in the project's repository with Read, Glob and Grep only. Its
``<plan>`` block is validated in code; invalid output is retried once with the errors
(never the previous output), and a second invalid answer fails with nothing written.
"""

import threading
from pathlib import Path
from typing import Any

from spoolhq.core.tokens import weighted_tokens
from spoolhq.services.agents import AgentEvent, AgentPolicy, AgentRunner, Budget, Outcome, RunResult
from spoolhq.services.agents.runner import RawCallback
from spoolhq.services.planner.model import InvalidPlan, PlannerError, PlanResult
from spoolhq.services.planner.prompt import render_planner_prompt
from spoolhq.services.planner.store import load_existing, write_plan
from spoolhq.services.planner.validate import check_plan, parse_plan
from spoolhq.services.projects import (
    ProjectError,
    load_project,
    project_dir,
)
from spoolhq.services.projects import template_description as stored_description

PLANNER_MAX_TURNS = 30
SPEC_FILE = "CONTEXT.md"
PROMPTS_DIR = "prompts"


def _ignore(_event: AgentEvent) -> None:
    pass


def read_spec(workspace: Path) -> str:
    try:
        return (workspace / SPEC_FILE).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise PlannerError(f"no {SPEC_FILE} in {workspace}: write the spec there first") from None
    except (OSError, UnicodeDecodeError) as exc:
        raise PlannerError(f"cannot read {SPEC_FILE}: {exc}") from exc


def generate_plan(
    project: str,
    runner: AgentRunner,
    *,
    projects_dir: Path,
    home: Path,
    template_description: str | None = None,
    model: str | None = None,
    on_raw: RawCallback | None = None,
    cancel: threading.Event,
) -> PlanResult:
    """Plan ``project`` from its ``CONTEXT.md`` and write the drafts.

    ``home`` is the SpoolHQ home (denied to the agent). Without ``template_description``
    the workspace's ``TEMPLATE.md`` is used, if there is one. Raises PlannerError before the
    agent starts (bad project, invalid ticket files, no spec) and whatever
    ``runner.run`` raises then; everything after the agent started is in the result.
    """
    try:
        settings = load_project(project, projects_dir=projects_dir)
        if template_description is None:
            # The description saved by `spool init --template` (TEMPLATE.md).
            template_description = stored_description(project, projects_dir=projects_dir)
    except ProjectError as exc:
        raise PlannerError(str(exc)) from exc
    workspace = project_dir(project, projects_dir)
    spec = read_spec(workspace)
    existing = load_existing(project, projects_dir=projects_dir)
    test_command = settings.commands.test
    policy = AgentPolicy.read_only_for(settings.repo_path, home, role="planner")
    limit = settings.agents.budget_per_ticket
    results: list[RunResult] = []
    errors: list[str] = []

    def finish(
        error: str | None, written: tuple[str, ...] = (), deleted: tuple[str, ...] = ()
    ) -> PlanResult:
        costs = [r.cost_micro_usd for r in results if r.cost_micro_usd is not None]
        return PlanResult(
            outcome=results[-1].outcome,
            error=error,
            written=written,
            deleted=deleted,
            kept=tuple(ticket.id for ticket in existing.kept),
            attempts=len(results),
            input_tokens=sum(r.input_tokens for r in results),
            output_tokens=sum(r.output_tokens for r in results),
            cache_read_tokens=sum(r.cache_read_tokens for r in results),
            cost_micro_usd=sum(costs) if costs else None,
        )

    final: list[str] = []

    def capture(message: dict[str, Any]) -> None:
        # The result's full final text; RunResult.summary keeps only its end.
        if message.get("type") == "result" and isinstance(message.get("result"), str):
            final.append(message["result"])
        if on_raw is not None:
            on_raw(message)

    for _attempt in range(2):
        left = None
        if limit is not None and limit.tokens is not None:
            used = sum(
                weighted_tokens(r.input_tokens, r.output_tokens, r.cache_read_tokens)
                for r in results
            )
            if used >= limit.tokens:
                return finish(f"budget used up: {used:,} of {limit.tokens:,} weighted tokens")
            left = limit.tokens - used
        final.clear()
        prompt = render_planner_prompt(
            spec,
            existing,
            test_command,
            template_description=template_description,
            previous_errors=errors or None,
            override_dir=workspace / PROMPTS_DIR,
        )
        result = runner.run(
            prompt,
            policy,
            Budget(max_turns=PLANNER_MAX_TURNS, max_usd=None, max_tokens=left),
            model=model,
            on_event=_ignore,
            on_raw=capture,
            cancel=cancel,
        )
        results.append(result)
        if result.outcome is not Outcome.COMPLETED:
            detail = f": {result.error}" if result.error else ""
            return finish(f"planner run ended: {result.outcome.value}{detail}")
        try:
            checked = check_plan(
                parse_plan(final[-1] if final else result.summary), existing, test_command
            )
        except InvalidPlan as exc:
            errors = exc.errors
            continue
        deleted = write_plan(project, checked.drafts, existing, projects_dir=projects_dir)
        return finish(None, tuple(ticket.id for ticket in checked.tickets), deleted)

    return finish("planner output invalid: " + "; ".join(errors))
