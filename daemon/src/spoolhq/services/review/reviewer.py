"""``review()``: one independent, read-only agent run that checks a ticket's diff.

Each attempt is a fresh run with a fresh prompt. Invalid output is retried once with
the validation errors (never the previous output); a second invalid answer becomes
``needs_human``. Run outcomes other than ``completed`` are passed through for the run
loop (T13) to handle.
"""

import threading
from pathlib import Path
from typing import Any

from spoolhq.services.agents import (
    AgentEvent,
    AgentPolicy,
    AgentRunner,
    Budget,
    Outcome,
    RunResult,
)
from spoolhq.services.agents.runner import EventCallback, RawCallback
from spoolhq.services.context import escape_closing_tag, render_template
from spoolhq.services.review.diff import trim_diff
from spoolhq.services.review.model import ItemVerdict, ReviewInputs, ReviewResult
from spoolhq.services.review.verdict import InvalidVerdict, ParsedVerdict, parse_verdict

REVIEWER_TEMPLATE = "reviewer.md.j2"
DEFAULT_BUDGET = Budget(max_turns=20, max_usd=None, max_tokens=None, timeout_s=600)


def _ignore(_event: AgentEvent) -> None:
    pass


def _gate_word(checked: bool | None) -> str | None:
    return None if checked is None else ("passed" if checked else "failed")


def render_review_prompt(
    inputs: ReviewInputs,
    diff: str,
    *,
    previous_errors: list[str] | None = None,
    override_dir: Path | None = None,
) -> str:
    """The reviewer's prompt; every untrusted value is escaped for its own block."""
    variables: dict[str, Any] = {
        "items": [
            {
                "index": index,
                "text": escape_closing_tag(text, "done_when"),
                "gate": _gate_word(inputs.gate_checked.get(index)),
            }
            for index, text in enumerate(inputs.done_when, start=1)
        ],
        "previous_errors": previous_errors or None,
        "ticket": {
            name: escape_closing_tag(value, "ticket")
            for name, value in (
                ("id", inputs.ticket_id),
                ("title", inputs.title),
                ("body", inputs.body),
            )
        },
        "gates": [
            {
                "name": escape_closing_tag(gate.name, "gates"),
                "command": escape_closing_tag(gate.command, "gates"),
                "status": escape_closing_tag(gate.status, "gates"),
            }
            for gate in inputs.gate_summary
        ],
        "diff": escape_closing_tag(diff, "diff"),
    }
    text, _ = render_template(REVIEWER_TEMPLATE, variables, override_dir=override_dir)
    return text


def _items(inputs: ReviewInputs, parsed: ParsedVerdict) -> tuple[ItemVerdict, ...]:
    """One entry per item, in order; gate-checked items take the gates' answer."""
    by_index = {item.index: item for item in parsed.items}
    items = []
    for index, text in enumerate(inputs.done_when, start=1):
        said = by_index[index]
        if index in inputs.gate_checked:
            met = inputs.gate_checked[index]
            reason = f"checked by the gates: {_gate_word(met)}"
            items.append(ItemVerdict(index, text, met, reason, "gates"))
        else:
            items.append(ItemVerdict(index, text, said.met, said.reason, "reviewer"))
    return tuple(items)


def review(
    inputs: ReviewInputs,
    runner: AgentRunner,
    *,
    home: Path,
    budget: Budget | None = None,
    model: str | None = None,
    override_dir: Path | None = None,
    on_event: EventCallback | None = None,
    on_raw: RawCallback | None = None,
    cancel: threading.Event,
) -> ReviewResult:
    """Review ``inputs`` with a read-only agent in ``inputs.worktree``.

    ``home`` is the SpoolHQ home (denied to the agent); ``override_dir`` the workspace's
    ``prompts/`` folder. Raises ValueError if the ticket has no "Done when" items, and
    whatever ``runner.run`` raises before the agent starts.
    """
    if not inputs.done_when:
        raise ValueError(f"ticket {inputs.ticket_id} has no 'Done when' items to review")
    policy = AgentPolicy.read_only_for(inputs.worktree, home)
    diff, trimmed = trim_diff(inputs.diff)
    results: list[RunResult] = []
    errors: list[list[str]] = []

    def finish(**fields: Any) -> ReviewResult:
        costs = [r.cost_micro_usd for r in results if r.cost_micro_usd is not None]
        return ReviewResult(
            run_outcome=results[-1].outcome,
            attempts=len(results),
            invalid_errors=tuple(
                f"attempt {number}: {error}"
                for number, attempt in enumerate(errors, start=1)
                for error in attempt
            ),
            diff_trimmed=trimmed,
            input_tokens=sum(r.input_tokens for r in results),
            output_tokens=sum(r.output_tokens for r in results),
            cost_micro_usd=sum(costs) if costs else None,
            reset_at=results[-1].reset_at,
            **fields,
        )

    final: list[str] = []

    def capture(message: dict[str, Any]) -> None:
        # The result's full final text; RunResult.summary keeps only its end.
        if message.get("type") == "result" and isinstance(message.get("result"), str):
            final.append(message["result"])
        if on_raw is not None:
            on_raw(message)

    for _attempt in range(2):
        final.clear()
        prompt = render_review_prompt(
            inputs,
            diff,
            previous_errors=errors[-1] if errors else None,
            override_dir=override_dir,
        )
        result = runner.run(
            prompt,
            policy,
            budget or DEFAULT_BUDGET,
            model=model,
            on_event=on_event or _ignore,
            on_raw=capture,
            cancel=cancel,
        )
        results.append(result)
        if result.outcome is not Outcome.COMPLETED:
            return finish(verdict=None, items=(), summary=result.error or "")
        try:
            parsed = parse_verdict(
                final[-1] if final else result.summary,
                len(inputs.done_when),
                gate_checked=inputs.gate_checked,
            )
        except InvalidVerdict as exc:
            errors.append(exc.errors)
            continue
        return finish(verdict=parsed.verdict, items=_items(inputs, parsed), summary=parsed.summary)

    flat = "; ".join(error for attempt in errors for error in attempt)
    return finish(
        verdict="needs_human",
        items=(),
        summary=f"reviewer returned invalid output twice: {flat}",
    )
