"""services/context: fitting the trimmable inputs into the character budget."""

import re

from spoolhq.services.context import RepoDocs, build_implementer_prompt
from spoolhq.services.context.budget import (
    Trimmed,
    cap_excerpt,
    keep_head,
    keep_newest_entries,
    newest_entries,
    newest_lines,
    select_spec,
    words,
)
from tests.services.context.conftest import block, fixture_inputs, fixture_text

NONE = RepoDocs()


def base_chars(**changes: object) -> int:
    """The prompt's size with no trimmable input, for budgets relative to it."""
    return build_implementer_prompt(fixture_inputs(spec=None, repo_docs=NONE, **changes)).chars


def fenced_content(text: str, tag: str) -> str:
    content = block(text, tag)
    return content.split("```\n", 1)[1].rsplit("\n```", 1)[0]


def test_decisions_keep_the_newest_entries() -> None:
    decisions = "# Decisions\n\n" + "".join(
        f"## {i}\n\nDecision number {i}, with a reason.\n\n" for i in range(1, 101)
    )
    max_chars = base_chars() + 2_000
    prompt = build_implementer_prompt(
        fixture_inputs(
            spec=None,
            repo_docs=RepoDocs(decisions_md=decisions),
            max_chars=max_chars,
            decisions_lines=1_000,
        )
    )

    assert prompt.chars <= max_chars
    match = re.search(r"\[trimmed: kept the last (\d+) of 100 entries\]", prompt.text)
    assert match is not None
    kept = int(match[1])
    assert 0 < kept < 100
    numbers = [
        int(n) for n in re.findall(r"^## (\d+)$", fenced_content(prompt.text, "decisions"), re.M)
    ]
    assert numbers == list(range(101 - kept, 101))
    assert prompt.cuts == (f"DECISIONS.md: {match[0]}",)


def test_long_claude_md_keeps_its_beginning() -> None:
    line = "- A convention line that is exactly sixty characters long.\n"
    claude_md = (line * 700)[:41_219] + "\n"
    assert len(claude_md) == 41_220
    prompt = build_implementer_prompt(
        fixture_inputs(spec=None, repo_docs=RepoDocs(claude_md=claude_md))
    )

    content = fenced_content(prompt.text, "claude_md")
    assert len(content) <= 16_000
    assert claude_md.startswith(content + "\n")
    note = f"[trimmed: kept the first {len(content) + 1:,} of 41,220 characters]"
    assert note in prompt.text


def big_spec() -> str:
    filler = "Invoices, reminders and receipts are emailed every month to owners.\n" * 30
    workspace = (
        "Each project has a workspace folder with a project.yaml holding its settings.\n"
        "The settings are validated by Pydantic and errors name the field.\n"
    )
    return (
        "# Demo app\n\nIntroduction to the app.\n\n"
        f"## Billing\n\n{filler}\n"
        f"## Workspaces and settings\n\n{workspace}\n"
        f"## Notifications\n\n{filler}\n"
        f"## Reports\n\n{filler}\n"
    )


def test_large_spec_keeps_the_outline_and_relevant_sections() -> None:
    spec = big_spec()
    max_chars = base_chars() + 2_000
    prompt = build_implementer_prompt(
        fixture_inputs(spec=spec, repo_docs=NONE, max_chars=max_chars)
    )

    content = fenced_content(prompt.text, "spec")
    headings = [line for line in spec.splitlines() if line.startswith("#")]
    assert [line for line in content.splitlines() if line.startswith("#")] == headings
    assert "Each project has a workspace folder" in content
    assert "Invoices, reminders" not in content
    assert "[trimmed: kept the outline and 1 of 4 sections]" in prompt.text
    assert prompt.chars <= max_chars


def test_unused_room_flows_on() -> None:
    progress = "".join(f"## T{i:02d}\n\n{'Progress detail. ' * 20}\n\n" for i in range(100))
    prompt = build_implementer_prompt(
        fixture_inputs(
            spec=None,
            repo_docs=RepoDocs(claude_md="", progress_md=progress),
            progress_entries=1_000,
        )
    )
    content = fenced_content(prompt.text, "progress_log")
    assert 23_000 < len(content) <= 24_000
    assert "<claude_md>\n" not in prompt.text


def test_fixture_docs_fit_untrimmed() -> None:
    prompt = build_implementer_prompt(fixture_inputs())
    assert fenced_content(prompt.text, "decisions") == fixture_text("DECISIONS.md").rstrip("\n")


# The trimmers on their own ----------------------------------------------------------


def test_cap_excerpt() -> None:
    assert cap_excerpt("short") == "short"
    text = "a" * 6_000 + "b" * 42_000 + "c" * 2_000
    assert cap_excerpt(text) == "a" * 6_000 + "\n[… 42,000 characters cut …]\n" + "c" * 2_000


def test_words() -> None:
    assert words("The Workspace, settings: of a café v2.0 abcd") == {
        "workspace",
        "settings",
        "abcd",
    }


def test_keep_head_with_no_room() -> None:
    assert keep_head("one\ntwo\n", 5) == Trimmed("")


def test_entries_without_headings_keep_the_last_lines() -> None:
    text = "".join(f"line {i}\n" for i in range(1_000))
    trimmed = keep_newest_entries(text, 400, cap=24_000)
    assert trimmed.text.endswith("line 999\n")
    assert trimmed.note == f"[trimmed: kept the last {trimmed.text.count(chr(10))} of 1,000 lines]"
    assert keep_newest_entries(text, 50, cap=24_000) == Trimmed("")


def test_entries_keep_the_preamble_when_it_fits() -> None:
    text = "# Log\n\n" + "".join(f"## {i}\nEntry {i}.\n" for i in range(20))
    trimmed = keep_newest_entries(text, len(text) + 50, cap=len(text) - 1)
    assert trimmed.text.startswith("# Log\n\n## ")
    assert trimmed.text.endswith("## 19\nEntry 19.\n")
    assert trimmed.note is not None and "kept the last" in trimmed.note
    small = keep_newest_entries("# Log\n" + "x" * 200 + "\n## 1\nOne.\n", 160, cap=24_000)
    assert small == Trimmed("## 1\nOne.\n", "[trimmed: kept all 1 entries, left out the preamble]")
    assert keep_newest_entries("## 1\n" + "x" * 500 + "\n", 120, cap=24_000) == Trimmed("")


def test_spec_without_sections_or_room_for_the_outline_keeps_its_beginning() -> None:
    plain = "".join(f"Line {i} of the spec.\n" for i in range(400))
    trimmed = select_spec(plain, 1_000, ticket_words=set())
    assert plain.startswith(trimmed.text)
    assert trimmed.note is not None and "kept the first" in trimmed.note

    headings = "".join(f"## Heading number {i}\nBody.\n" for i in range(200))
    trimmed = select_spec(headings, 500, ticket_words=set())
    assert trimmed.note is not None and "kept the first" in trimmed.note


def test_spec_ties_keep_document_order() -> None:
    spec = "## A\n" + "x\n" * 60 + "## B\n" + "y\n" * 60 + "## C\n" + "z\n" * 60
    trimmed = select_spec(spec, 260, ticket_words=set())
    assert trimmed.text.startswith("## A\nx\n")
    assert "## B\n## C\n" in trimmed.text


def test_newest_entries_keeps_the_preamble_and_the_last_entries() -> None:
    log = "# Progress\n\nNewest at the bottom.\n\n" + "".join(
        f"## T{i:02d}\n\nDid {i}.\n\n" for i in range(1, 6)
    )
    kept = newest_entries(log, 3)
    assert kept == "# Progress\n\nNewest at the bottom.\n\n" + "".join(
        f"## T{i:02d}\n\nDid {i}.\n\n" for i in range(3, 6)
    )
    assert newest_entries(log, 5) == log
    assert newest_entries("no headings\n", 1) == "no headings\n"


def test_newest_lines_counts_only_non_blank_lines() -> None:
    decisions = "# Decisions\n\n" + "".join(f"{i}. Decision {i}.\n" for i in range(1, 31)) + "\n"
    kept = newest_lines(decisions, 20)
    assert kept.splitlines()[0] == "11. Decision 11."
    assert kept.endswith("30. Decision 30.\n\n")
    assert len([line for line in kept.splitlines() if line]) == 20
    assert newest_lines("a\n\nb\n", 5) == "a\n\nb\n"


def test_the_prompt_takes_only_the_newest_history() -> None:
    progress = "# Progress\n\n" + "".join(f"## T{i:02d}\n\nDid {i}.\n\n" for i in range(1, 11))
    decisions = "".join(f"{i}. Decision {i}.\n" for i in range(1, 51))
    prompt = build_implementer_prompt(
        fixture_inputs(
            spec=None,
            repo_docs=RepoDocs(progress_md=progress, decisions_md=decisions),
            progress_entries=2,
            decisions_lines=4,
        )
    )
    progress_block = fenced_content(prompt.text, "progress_log")
    assert re.findall(r"^## (T\d+)$", progress_block, re.M) == ["T09", "T10"]
    assert fenced_content(prompt.text, "decisions").splitlines() == [
        f"{i}. Decision {i}." for i in range(47, 51)
    ]
    assert prompt.cuts == ()
    assert (
        "Older entries are in PROGRESS.md and DECISIONS.md; grep them when the ticket "
        "touches an earlier decision." in prompt.text
    )
    without = build_implementer_prompt(fixture_inputs(spec=None, repo_docs=NONE))
    assert "Older entries" not in without.text
