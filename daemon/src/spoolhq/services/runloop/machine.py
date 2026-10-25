"""The state machine of one run, as plain functions over a ``RunContext``.

``drive`` runs attempts until the run ends: implement, commit, gates, review, then
integrate an approved attempt. Retry counters come from the run's attempt rows, so a
resumed run (after a pause or a crash) counts the same way; an ``interrupted`` attempt
never counts. See ``docs/run-loop.md``.
"""

import dataclasses
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from spoolhq.services.agents import AgentPolicy, Budget, Outcome, RunResult
from spoolhq.services.context import (
    ContextInputs,
    DependencyView,
    GateFailure,
    PreviousAttempt,
    RepoDocs,
    ReviewNote,
    TicketView,
    build_implementer_prompt,
    extract_progress_note,
)
from spoolhq.services.gates import GateRun, check_done_when
from spoolhq.services.git import (
    conclude_merge,
    conflict_files,
    merge_head,
    run_git,
    unresolved_files,
)
from spoolhq.services.review import GateLine, ReviewInputs, ReviewResult, review
from spoolhq.services.runloop.integrator import IntegrationStatus
from spoolhq.services.runloop.model import Ending, EndKind, RunContext
from spoolhq.services.runs import (
    ArtifactName,
    Attempt,
    AttemptKind,
    AttemptStatus,
    EventKind,
    append_transcript,
    attempt_dir,
    attempt_files,
    write_artifact,
)
from spoolhq.services.tickets import list_tickets

IMPLEMENTER_MAX_TURNS = 100
PROMPTS_DIR = "prompts"
CONTEXT_FILE = "CONTEXT.md"
EARLY_STOPS = (Outcome.TIMED_OUT, Outcome.MAX_TURNS, Outcome.BUDGET_EXHAUSTED)
# Where the next attempt continues after the last finished one (see next_kind).
_NEXT_KIND = {
    AttemptStatus.GATES_FAILED: AttemptKind.GATE_RETRY,
    AttemptStatus.CHANGES_REQUESTED: AttemptKind.REVIEW_RETRY,
    AttemptStatus.ERROR: AttemptKind.GATE_RETRY,  # an implementer that stopped early
}

Step = Ending | AttemptKind


def _read(path: Path) -> str | None:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else None


def _git(ctx: RunContext, *args: str) -> str:
    return run_git(args, ctx.worktree.path).check().stdout


def _retries(limit: int) -> str:
    return f"{limit} retr{'y' if limit == 1 else 'ies'}"


# --- deciding -------------------------------------------------------------------------


def next_kind(attempts: list[Attempt]) -> AttemptKind | None:
    """The kind of attempt a resumed run starts with; None when the last was approved
    (only the integration is left)."""
    if not attempts:
        return AttemptKind.INITIAL
    last = attempts[-1]
    if last.status in (AttemptStatus.INTERRUPTED, AttemptStatus.RUNNING):
        return last.kind
    if last.status is AttemptStatus.APPROVED:
        return None
    return _NEXT_KIND.get(last.status, AttemptKind.INITIAL)


def retry_or_block(ctx: RunContext, kind: AttemptKind, what: str, detail: str = "") -> Step:
    """Start a retry of ``kind`` if the project's limit allows another, else block."""
    limits = ctx.project.limits
    limit = limits.gate_retries if kind is AttemptKind.GATE_RETRY else limits.review_retries
    used = sum(
        1
        for attempt in ctx.run_log.list_attempts(ctx.run.id)
        if attempt.kind is kind and attempt.status is not AttemptStatus.INTERRUPTED
    )
    if used < limit:
        return kind
    suffix = f": {detail}" if detail else ""
    return Ending(EndKind.BLOCKED, f"{what} after {_retries(limit)}{suffix}")


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


def previous_attempt(ctx: RunContext, kind: AttemptKind) -> PreviousAttempt | None:
    """What went wrong last time, read from the last finished attempt's files."""
    if kind is AttemptKind.INITIAL:
        return None
    finished = [
        attempt
        for attempt in ctx.run_log.list_attempts(ctx.run.id)
        if attempt.status not in (AttemptStatus.RUNNING, AttemptStatus.INTERRUPTED)
    ]
    if not finished:
        return None
    last = finished[-1]
    files = attempt_files(ctx.workspace, last)
    gates: dict[str, Any] = {}
    reviewed: dict[str, Any] = {}
    if ArtifactName.GATES.value in files:
        gates = json.loads(files[ArtifactName.GATES.value].read_text(encoding="utf-8"))
    if ArtifactName.REVIEW.value in files:
        reviewed = json.loads(files[ArtifactName.REVIEW.value].read_text(encoding="utf-8"))
    note = None
    conflicts: tuple[str, ...] = ()
    if kind is AttemptKind.CONFLICT_RETRY:
        conflicts = conflict_files(ctx.worktree.path)
        note = (
            f"SpoolHQ merged the latest {ctx.project.default_branch} into your branch and these "
            "files conflict. Resolve every conflict marker in them and keep the intent of both "
            "sides; don't run git commands that change anything."
        )
    elif "stopped" in gates:
        note = (
            f"Your last attempt stopped before the checks ran ({gates['stopped']}). "
            "Your changes so far are committed; continue from them."
        )
    elif "stopped" in reviewed:
        note = (
            f"The reviewer stopped before giving a verdict ({reviewed['stopped']}). "
            'Check your work against every "Done when" item.'
        )
    tests = [name for result in gates.get("results", []) for name in result["failing_tests"]]
    pr_review = None
    if kind is AttemptKind.PR_CHANGES:  # stored by polling.py when it starts this attempt
        events = ctx.run_log.events_since(0, run_id=ctx.run.id, limit=100_000)
        logged = [e.payload for e in events if e.kind is EventKind.LOG and "pr_review" in e.payload]
        pr_review = str(logged[-1]["pr_review"]) if logged else None
    return PreviousAttempt(
        kind=kind.value,
        number=last.number,
        failing_tests=tuple(dict.fromkeys(tests)),
        gate_failures=tuple(GateFailure(**failure) for failure in gates.get("failures", [])),
        review_notes=tuple(
            ReviewNote(item["item"], item["met"], item["reason"])
            for item in reviewed.get("items", [])
            if not item["met"]
        ),
        conflict_files=conflicts,
        system_note=note,
        pr_review=pr_review,
    )


def implementer_prompt(ctx: RunContext, kind: AttemptKind) -> str:
    listing = list_tickets(ctx.project.name, projects_dir=ctx.projects_dir)
    by_id = {ticket.id: ticket for ticket in listing.tickets}
    meta = ctx.ticket.meta
    repo = ctx.project.repo_path
    inputs = ContextInputs(
        ticket=TicketView(
            id=ctx.ticket_id,
            title=meta.title,
            body=ctx.ticket.body,
            depends_on=tuple(
                DependencyView(dep, by_id[dep].meta.title, by_id[dep].meta.status)
                if dep in by_id
                else DependencyView(dep, "(not found)", "missing")
                for dep in meta.depends_on
            ),
            review_required=meta.review_required,
        ),
        spec=_read(ctx.workspace / CONTEXT_FILE),
        repo_docs=RepoDocs(
            claude_md=_read(repo / "CLAUDE.md"),
            progress_md=_read(repo / "PROGRESS.md"),
            decisions_md=_read(repo / "DECISIONS.md"),
        ),
        commands=ctx.project.commands.for_implementer(),
        previous=previous_attempt(ctx, kind),
        max_chars=ctx.project.context.max_chars,
        progress_entries=ctx.project.context.progress_entries,
        decisions_lines=ctx.project.context.decisions_lines,
    )
    return build_implementer_prompt(inputs, override_dir=ctx.workspace / PROMPTS_DIR).text


# --- the steps ------------------------------------------------------------------------


def implement(ctx: RunContext, attempt: Attempt) -> tuple[RunResult, str]:
    """Run the implementer with the writing policy; its result and full final text."""
    prompt = implementer_prompt(ctx, attempt.kind)
    policy = AgentPolicy.for_worktree(
        ctx.worktree.path, ctx.project.commands.for_implementer(), ctx.home
    )
    budget = ctx.project.agents.budget_per_ticket
    left = None
    if budget is not None and budget.tokens is not None:
        left = max(budget.tokens - ctx.run_log.run_usage(ctx.run.id).weighted_tokens, 1)
    final: list[str] = []

    def on_raw(message: dict[str, Any]) -> None:
        # The full final text; RunResult.summary keeps only its last 4,000 characters.
        if message.get("type") == "result" and isinstance(message.get("result"), str):
            final.append(message["result"])
        append_transcript(attempt, message)

    result = ctx.agents.implementer.run(
        prompt,
        policy,
        Budget(max_turns=IMPLEMENTER_MAX_TURNS, max_usd=None, max_tokens=left),
        on_event=lambda _event: None,
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
    gate_run = ctx.gates(
        ctx.worktree.path,
        ctx.project.commands.model_dump(),
        ctx.project.gates.timeouts.model_dump(),
        attempt_dir(ctx.workspace, attempt),
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
    resolving = attempt.kind is AttemptKind.CONFLICT_RETRY
    conflicted = conflict_files(ctx.worktree.path) if resolving else ()
    result, final_text = implement(ctx, attempt)
    if resolving and result.outcome in (Outcome.COMPLETED, *EARLY_STOPS):
        # Committing would conclude the merge, so the markers are checked first.
        if ending := check_resolved(ctx, attempt, conflicted):
            return ending
    if result.outcome in EARLY_STOPS:
        commit(ctx, attempt, label)  # keep what it did; the retry continues from it
    if result.outcome is not Outcome.COMPLETED:
        return agent_stopped(
            ctx, attempt, "implementer", result.outcome, result.error, result.reset_at
        )
    note = extract_progress_note(final_text)
    if note is not None:
        ctx.run = ctx.run_log.set_progress_note(ctx.run.id, note)
    commit(ctx, attempt, label)
    if ending := interrupted(ctx, attempt):
        return ending

    gate_run = run_gates(ctx, attempt, label)
    if not gate_run.passed:
        ctx.run_log.finish_attempt(attempt.id, AttemptStatus.GATES_FAILED)
        first = gate_run.first_failure
        command = first.command if first is not None else ""
        return retry_or_block(ctx, AttemptKind.GATE_RETRY, "gates failed", command)
    if ending := interrupted(ctx, attempt):
        return ending

    reviewed = run_review(ctx, attempt, gate_run)
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
    if reviewed.verdict == "approve":
        ctx.run_log.finish_attempt(attempt.id, AttemptStatus.APPROVED)
        return integrate(ctx)
    if reviewed.verdict == "needs_human":
        ctx.run_log.finish_attempt(attempt.id, AttemptStatus.NEEDS_HUMAN)
        return Ending(EndKind.BLOCKED, f"the reviewer asked for a person: {reviewed.summary}")
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
