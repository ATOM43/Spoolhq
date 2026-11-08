"""The state machine of one run, as plain functions over a ``RunContext``.

``drive`` runs attempts until the run ends: implement, commit, gates, review, then
integrate an approved attempt. Retry counters come from the run's attempt rows, so a
resumed run (after a pause or a crash) counts the same way; an ``interrupted`` attempt
never counts. See ``docs/run-loop.md``.
"""

import dataclasses
import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from spoolhq.services.agents import AgentPolicy, Budget, Outcome, RunResult
from spoolhq.services.context import extract_progress_note
from spoolhq.services.gates import GateResult, GateRun, check_done_when
from spoolhq.services.git import (
    conclude_merge,
    conflict_files,
    merge_head,
    run_git,
    unresolved_files,
)
from spoolhq.services.review import GateLine, ReviewInputs, ReviewResult, review
from spoolhq.services.runloop.integrator import IntegrationStatus
from spoolhq.services.runloop.model import Ending, EndKind, RunContext, record_step
from spoolhq.services.runloop.prompting import implementer_prompt
from spoolhq.services.runloop.transcript import Recorder
from spoolhq.services.runs import (
    ArtifactName,
    Attempt,
    AttemptKind,
    AttemptStatus,
    EventKind,
    RunLog,
    append_transcript,
    attempt_dir,
    write_artifact,
)

IMPLEMENTER_MAX_TURNS = 100
RETRIES_RESET = "retries_reset_after"
"""Log-event key: retries count only attempts after this attempt id (an unblock)."""
PROMPTS_DIR = "prompts"
EARLY_STOPS = (Outcome.TIMED_OUT, Outcome.MAX_TURNS, Outcome.BUDGET_EXHAUSTED)
# Where the next attempt continues after the last finished one (see next_kind).
_NEXT_KIND = {
    AttemptStatus.GATES_FAILED: AttemptKind.GATE_RETRY,
    AttemptStatus.CHANGES_REQUESTED: AttemptKind.REVIEW_RETRY,
    AttemptStatus.ERROR: AttemptKind.GATE_RETRY,  # an implementer that stopped early
}

Step = Ending | AttemptKind


def _git(ctx: RunContext, *args: str) -> str:
    return run_git(args, ctx.worktree.path).check().stdout


def _retries(limit: int) -> str:
    return f"{limit} retr{'y' if limit == 1 else 'ies'}"


# --- deciding -------------------------------------------------------------------------


def next_kind(attempts: list[Attempt]) -> AttemptKind | None:
    """The kind of attempt a resumed run starts with; None when the last was approved
    or went to a person (only the integration is left)."""
    if not attempts:
        return AttemptKind.INITIAL
    last = attempts[-1]
    if last.status in (AttemptStatus.INTERRUPTED, AttemptStatus.RUNNING):
        return last.kind
    if last.status in (AttemptStatus.APPROVED, AttemptStatus.NEEDS_HUMAN):
        return None
    return _NEXT_KIND.get(last.status, AttemptKind.INITIAL)


def retry_or_block(ctx: RunContext, kind: AttemptKind, what: str, detail: str = "") -> Step:
    """Start a retry of ``kind`` if the project's limit allows another, else block."""
    limits = ctx.project.limits
    limit = limits.gate_retries if kind is AttemptKind.GATE_RETRY else limits.review_retries
    if retries_used(ctx.run_log, ctx.run.id, kind) < limit:
        return kind
    suffix = f": {detail}" if detail else ""
    return Ending(EndKind.BLOCKED, f"{what} after {_retries(limit)}{suffix}")


def retries_used(run_log: RunLog, run_id: int, kind: AttemptKind) -> int:
    """The run's ``kind`` retries so far, counted from its latest unblock that reset them."""
    after = 0
    for event in run_log.events_since(0, run_id=run_id, limit=100_000):
        reset = event.payload.get(RETRIES_RESET) if event.kind is EventKind.LOG else None
        if isinstance(reset, int):
            after = reset
    return sum(
        1
        for attempt in run_log.list_attempts(run_id)
        if attempt.id > after
        and attempt.kind is kind
        and attempt.status is not AttemptStatus.INTERRUPTED
    )


def over_budget(ctx: RunContext) -> str | None:
    """Why the ticket's budget (``agents.budget_per_ticket``) is used up, or None."""
    budget = ctx.project.agents.budget_per_ticket
    if budget is None:
        return None
    usage = ctx.run_log.run_usage(ctx.run.id)
    if budget.tokens is not None and usage.weighted_tokens >= budget.tokens:
        return f"budget used up: {usage.weighted_tokens:,} of {budget.tokens:,} weighted tokens"
    if budget.usd is not None and usage.cost_micro_usd is not None:
        spent = usage.cost_micro_usd / 1_000_000
        if spent >= budget.usd:
            return f"budget used up: ${spent:,.2f} of ${budget.usd:,.2f}"
    return None


def interrupted(ctx: RunContext, attempt: Attempt | None) -> Ending | None:
    """Stop between steps if another thread asked for it.

    A daemon shutdown sets ``stop`` and ``cancel`` (to stop the agent at once), so
    ``stop`` is checked first: the run is left for startup recovery, not torn down.
    """
    flags = ctx.flags
    if flags.stop.is_set():
        status, ending = AttemptStatus.INTERRUPTED, Ending(EndKind.STOPPED)
    elif flags.cancel.is_set():
        status, ending = AttemptStatus.CANCELLED, Ending(EndKind.CANCELLED)
    elif flags.pause.is_set():
        status, ending = AttemptStatus.INTERRUPTED, Ending(EndKind.PAUSED, "paused by the user")
    else:
        return None
    if attempt is not None:
        ctx.run_log.finish_attempt(attempt.id, status)
    return ending


def agent_stopped(
    ctx: RunContext,
    attempt: Attempt,
    role: str,
    outcome: Outcome,
    error: str | None,
    reset_at: datetime | None,
) -> Step:
    """Turn an agent run that didn't complete into the run's next step."""
    log = ctx.run_log
    if outcome is Outcome.CANCELLED:
        return interrupted(ctx, attempt) or Ending(EndKind.CANCELLED)
    if outcome is Outcome.USAGE_LIMITED:
        # Paused, not failed: the cut-off attempt never counts against the retries.
        log.finish_attempt(attempt.id, AttemptStatus.INTERRUPTED)
        return Ending(EndKind.PAUSED, f"the {role} hit a usage limit", reset_at)
    if outcome not in EARLY_STOPS:  # error, a policy violation included: never retried
        log.finish_attempt(attempt.id, AttemptStatus.ERROR)
        return Ending(EndKind.BLOCKED, f"{role} error: {error or outcome}")
    if role == "implementer":
        write_artifact(attempt, ArtifactName.GATES, json.dumps({"stopped": outcome.value}))
        log.finish_attempt(attempt.id, AttemptStatus.ERROR)
        return retry_or_block(ctx, AttemptKind.GATE_RETRY, f"implementer stopped ({outcome})")
    write_artifact(attempt, ArtifactName.REVIEW, json.dumps({"stopped": outcome.value}))
    log.finish_attempt(attempt.id, AttemptStatus.CHANGES_REQUESTED)
    return retry_or_block(ctx, AttemptKind.REVIEW_RETRY, f"reviewer stopped ({outcome})")


# --- the prompt ------------------------------------------------------------------------


# --- the steps ------------------------------------------------------------------------


def implement(ctx: RunContext, attempt: Attempt) -> tuple[RunResult, str]:
    """Run the implementer with the writing policy; its result and full final text."""
    prompt = implementer_prompt(ctx, attempt.kind)
    policy = AgentPolicy.for_worktree(
        ctx.worktree.path, ctx.project.commands.for_implementer(), ctx.home
    )
    budget = ctx.project.agents.budget_per_ticket
    usage = ctx.run_log.run_usage(ctx.run.id)
    left = usd_left = None
    if budget is not None and budget.tokens is not None:
        left = max(budget.tokens - usage.weighted_tokens, 1)
    if budget is not None and budget.usd is not None:
        # API-billed backends stop mid-run at what is left (over_budget checks between steps).
        spent = Decimal(usage.cost_micro_usd or 0) / 1_000_000
        usd_left = max(Decimal(str(budget.usd)) - spent, Decimal("0.01")).quantize(
            Decimal("0.0001")
        )
    final: list[str] = []

    def on_raw(message: dict[str, Any]) -> None:
        # The full final text; RunResult.summary keeps only its last 4,000 characters.
        if message.get("type") == "result" and isinstance(message.get("result"), str):
            final.append(message["result"])
        append_transcript(attempt, message)

    result = ctx.agents.implementer.run(
        prompt,
        policy,
        Budget(max_turns=IMPLEMENTER_MAX_TURNS, max_usd=usd_left, max_tokens=left),
        on_event=Recorder(ctx.run_log, attempt),
        on_raw=on_raw,
        cancel=ctx.flags.cancel,
    )
    ctx.run_log.record_usage(
        attempt.id,
        result.input_tokens,
        result.output_tokens,
        result.cost_micro_usd,
        result.cache_read_tokens,
    )
    return result, final[-1] if final else result.summary


def commit(ctx: RunContext, attempt: Attempt, label: str) -> None:
    """Commit everything in the worktree; the files changed come from git."""
    before = _git(ctx, "rev-parse", "HEAD").strip()
    message = f"spool: {ctx.ticket_id} attempt {attempt.number}"
    sha = ctx.worktrees.commit_all(ctx.worktree, message)
    if sha is None and merge_head(ctx.worktree.path):  # a resolved merge with no change
        sha = conclude_merge(ctx.worktree.path, message)
    files = _git(ctx, "diff", "--name-only", before, sha).splitlines() if sha else []
    text = f"{sha[:7]} ({len(files)} files)" if sha else "no changes"
    ctx.phase("commit", f"{label} · commit · {text}", attempt)
    write_artifact(attempt, ArtifactName.DIFF, _git(ctx, "diff", f"{ctx.worktree.base_sha}...HEAD"))


def run_gates(ctx: RunContext, attempt: Attempt, label: str) -> GateRun:
    commands = ctx.project.commands.model_dump()

    def started(name: str, done: tuple[GateResult, ...]) -> None:
        # The Run tab's rows so far; output waits for gates.json.
        rows = [
            {
                "name": r.name,
                "command": r.command,
                "status": r.status.value,
                "duration_ms": round(r.duration_s * 1000),
            }
            for r in done
        ]
        extra = {"gate": name, "command": commands.get(name) or "", "done": rows}
        record_step(ctx.run_log, ctx.run.id, "gates", "running", attempt, extra)

    gate_run = ctx.gates(
        ctx.worktree.path,
        commands,
        ctx.project.gates.timeouts.model_dump(),
        attempt_dir(ctx.workspace, attempt),
        on_gate=started,
    )
    tests = [name for result in gate_run.results for name in result.failing_tests]
    data = {
        "passed": gate_run.passed,
        "results": [dataclasses.asdict(result) for result in gate_run.results],
        "failures": list(gate_run.to_gate_failures()),
    }
    write_artifact(attempt, ArtifactName.GATES, json.dumps(data, indent=2, default=str))
    first = gate_run.first_failure
    if first is None:
        text = "✓ passed"
    else:
        text = f"✗ {first.name}" + (f" ({len(set(tests))} failing)" if tests else "")
    ctx.phase("gates", f"{label} · gates · {text}", attempt)
    return gate_run


def _transcript(attempt: Attempt, message: dict[str, Any]) -> None:
    append_transcript(attempt, message)


def _worktree_state(ctx: RunContext) -> tuple[str, str]:
    return _git(ctx, "rev-parse", "HEAD"), _git(ctx, "status", "--porcelain", "-z")


def run_review(ctx: RunContext, attempt: Attempt, gate_run: GateRun) -> ReviewResult | None:
    """Review the committed diff; None if the reviewer changed the worktree."""
    commands = ctx.project.commands.model_dump()
    done_when = tuple(item.text for item in ctx.ticket.done_when)
    gate_checked = {}
    for index, item in enumerate(done_when, start=1):
        checks = check_done_when([item], commands, gate_run)
        if checks and checks[0].status != "not_a_gate":
            gate_checked[index] = checks[0].status == "passed"
    inputs = ReviewInputs(
        ticket_id=ctx.ticket_id,
        title=ctx.ticket.meta.title,
        body=ctx.ticket.body,
        done_when=done_when,
        gate_checked=gate_checked,
        diff=_git(ctx, "diff", f"{ctx.worktree.base_sha}...HEAD"),
        gate_summary=tuple(GateLine(r.name, r.command, r.status.value) for r in gate_run.results),
        worktree=ctx.worktree.path,
    )
    before = _worktree_state(ctx)
    result = review(
        inputs,
        ctx.agents.reviewer,
        home=ctx.home,
        override_dir=ctx.workspace / PROMPTS_DIR,
        on_raw=lambda message: _transcript(attempt, message),
        cancel=ctx.flags.cancel,
    )
    ctx.run_log.record_usage(
        attempt.id,
        result.input_tokens,
        result.output_tokens,
        result.cost_micro_usd,
        result.cache_read_tokens,
    )
    write_artifact(
        attempt, ArtifactName.REVIEW, json.dumps(dataclasses.asdict(result), default=str)
    )
    return result if _worktree_state(ctx) == before else None


def integrate(ctx: RunContext) -> Step:
    """Hand the approved work to the integrator. A conflict goes back to the implementer
    once, and gates failing on the merged code use the gate retries."""
    result = ctx.integrator.integrate(ctx)
    tid = ctx.ticket_id
    if result.status is not IntegrationStatus.HELD:
        ctx.step("integrate", "passed" if result.status is IntegrationStatus.MERGED else "failed")
    if result.status is IntegrationStatus.MERGED:
        detail = f" {result.message}" if result.message else ""
        ctx.phase("integrate", f"{tid} · integrate · merged{detail}")
        return Ending(EndKind.DONE)
    if result.status is IntegrationStatus.HELD:
        ctx.phase("integrate", result.message)
        return Ending(EndKind.HELD, result.message)
    ctx.phase("integrate", f"{tid} · integrate · {result.status}")
    if result.status is IntegrationStatus.GATES_FAILED:
        return retry_or_block(ctx, AttemptKind.GATE_RETRY, "gates failed", result.message)
    if result.status is IntegrationStatus.CONFLICT and not any(
        attempt.kind is AttemptKind.CONFLICT_RETRY
        and attempt.status is not AttemptStatus.INTERRUPTED
        for attempt in ctx.run_log.list_attempts(ctx.run.id)
    ):
        return AttemptKind.CONFLICT_RETRY
    return Ending(EndKind.BLOCKED, result.message)


def check_resolved(ctx: RunContext, attempt: Attempt, conflicted: tuple[str, ...]) -> Ending | None:
    """After a conflict retry: nothing unmerged and no marker left, else blocked."""
    left = unresolved_files(ctx.worktree.path, conflicted)
    if not left:
        return None
    ctx.run_log.finish_attempt(attempt.id, AttemptStatus.CONFLICT)
    return Ending(EndKind.BLOCKED, f"merge conflict with main in: {', '.join(left)}")


def attempt_once(ctx: RunContext, attempt: Attempt) -> Step:
    """One attempt: implement, commit, gates, review. The next step of the run."""
    label = f"{ctx.ticket_id} attempt {attempt.number}"
    ctx.phase("implement", f"{label} · implement ({attempt.kind})", attempt)
    ctx.step("implement", "running", attempt)
    resolving = attempt.kind is AttemptKind.CONFLICT_RETRY
    conflicted = conflict_files(ctx.worktree.path) if resolving else ()
    result, final_text = implement(ctx, attempt)
    if resolving and result.outcome in (Outcome.COMPLETED, *EARLY_STOPS):
        # Committing would conclude the merge, so the markers are checked first.
        if ending := check_resolved(ctx, attempt, conflicted):
            ctx.step("implement", "failed", attempt)
            return ending
    if result.outcome in EARLY_STOPS:
        commit(ctx, attempt, label)  # keep what it did; the retry continues from it
    if result.outcome is not Outcome.COMPLETED:
        if result.outcome not in (Outcome.CANCELLED, Outcome.USAGE_LIMITED):
            ctx.step("implement", "failed", attempt)
        return agent_stopped(
            ctx, attempt, "implementer", result.outcome, result.error, result.reset_at
        )
    note = extract_progress_note(final_text)
    if note is not None:
        ctx.run = ctx.run_log.set_progress_note(ctx.run.id, note)
    commit(ctx, attempt, label)
    ctx.step("implement", "passed", attempt)
    if ending := interrupted(ctx, attempt):
        return ending

    ctx.step("gates", "running", attempt)
    gate_run = run_gates(ctx, attempt, label)
    ctx.step("gates", "passed" if gate_run.passed else "failed", attempt)
    if not gate_run.passed:
        ctx.run_log.finish_attempt(attempt.id, AttemptStatus.GATES_FAILED)
        first = gate_run.first_failure
        command = first.command if first is not None else ""
        return retry_or_block(ctx, AttemptKind.GATE_RETRY, "gates failed", command)
    if ending := interrupted(ctx, attempt):
        return ending

    ctx.step("review", "running", attempt)
    reviewed = run_review(ctx, attempt, gate_run)
    passed = reviewed is not None and reviewed.verdict in ("approve", "needs_human")
    ctx.step("review", "passed" if passed else "failed", attempt)
    if reviewed is None:
        ctx.run_log.finish_attempt(attempt.id, AttemptStatus.ERROR)
        return Ending(EndKind.BLOCKED, "reviewer changed the worktree")
    if reviewed.verdict is None:
        return agent_stopped(
            ctx, attempt, "reviewer", reviewed.run_outcome, reviewed.summary, reviewed.reset_at
        )
    unmet = ", ".join(str(item.index) for item in reviewed.unmet())
    detail = f" (item {unmet})" if unmet and reviewed.verdict == "changes_requested" else ""
    ctx.phase("review", f"{label} · review · {reviewed.verdict}{detail}", attempt)
    if reviewed.verdict in ("approve", "needs_human"):
        # The gates passed; the merge policy sends a needs_human verdict to a person.
        approved = reviewed.verdict == "approve"
        status = AttemptStatus.APPROVED if approved else AttemptStatus.NEEDS_HUMAN
        ctx.run_log.finish_attempt(attempt.id, status)
        return integrate(ctx)
    ctx.run_log.finish_attempt(attempt.id, AttemptStatus.CHANGES_REQUESTED)
    return retry_or_block(ctx, AttemptKind.REVIEW_RETRY, "changes requested")


def drive(ctx: RunContext, kind: AttemptKind | None) -> Ending:
    """Run attempts from ``kind`` until the run ends; ``None`` starts at the integration."""
    step: Step = integrate(ctx) if kind is None else kind
    while not isinstance(step, Ending):
        if ending := interrupted(ctx, None):
            return ending
        if reason := over_budget(ctx):
            return Ending(EndKind.BLOCKED, reason)
        attempt = ctx.run_log.start_attempt(ctx.run.id, step, backend=ctx.agents.implementer.name)
        step = attempt_once(ctx, attempt)
    return step
