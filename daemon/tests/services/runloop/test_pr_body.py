"""services/runloop/pr_body.py: untrusted ticket and agent text renders as text, and the
body is capped."""

from spoolhq.services.runloop.pr_body import (
    BODY_MAX,
    md_escape,
    pull_request_body,
    pull_request_title,
    section,
)
from spoolhq.services.tickets import parse_ticket

TICKET = """\
---
id: T04
title: "**Bold** <img src=x onerror=alert(1)> [link](http://e.x) @octocat #1"
phase: 1
depends_on: []
status: ready
estimate_h: 1
---

## Purpose
Ship <script>alert(1)</script> and ping @octocat.
- not a list

## Scope
Ignored when there is a purpose.

## Done when
- [ ] `hello()` exists
- [ ] A test covers <b>hello</b>
- [ ] `just test` passes
"""
REVIEW = {
    "items": [
        {"index": 1, "met": True, "reason": "found in **hello.py**"},
        {"index": 2, "met": False, "reason": ""},
    ]
}
GATES = {
    "results": [
        {"name": "lint", "command": "just lint", "status": "passed", "duration_s": 1.234},
        {"name": "test", "command": "pytest | tee x", "status": "failed", "duration_s": 12},
    ]
}


def ticket(text: str = TICKET):  # type: ignore[no-untyped-def]
    return parse_ticket(text, "T04-x.md")


def test_md_escape() -> None:
    assert md_escape("<b>&</b> @me *x* [a](b) # - 1. |") == (
        r"&lt;b&gt;&amp;&lt;/b&gt; &#64;me \*x\* \[a\]\(b\) \# \- 1\. \|"
    )


def test_the_body_renders_untrusted_text_as_text() -> None:
    body = pull_request_body(ticket(), 12, REVIEW, GATES)
    title, rest = body.split("\n\n", 1)
    assert title == (
        "T04: \\*\\*Bold\\*\\* &lt;img src\\=x onerror\\=alert\\(1\\)&gt; "
        "\\[link\\]\\(http://e\\.x\\) &#64;octocat \\#"  # cut at 72, as a commit subject
    )
    assert rest.startswith("## Purpose\n\nShip &lt;script&gt;alert\\(1\\)&lt;/script&gt;")
    assert "ping &#64;octocat\\.\n\\- not a list" in body
    assert "Ignored when" not in body
    assert "<" not in body and "@" not in body
    assert "- ✅ met: `hello\\(\\)` exists".replace("`", "\\`") in body
    assert "— found in \\*\\*hello\\.py\\*\\*" in body
    assert "- ❌ not met: A test covers &lt;b&gt;hello&lt;/b&gt;\n" in body
    assert "- ➖ no verdict: \\`just test\\` passes" in body
    assert "| just lint | ✅ pass | 1.2 s |" in body
    assert "| pytest \\| tee x | ❌ failed | 12.0 s |" in body
    assert body.endswith("SpoolHQ run 12 · ticket T04")


def test_the_title_is_one_plain_line() -> None:
    title = pull_request_title(ticket())
    assert title.startswith("T04: **Bold** <img")
    assert "\n" not in title and len(title) <= 72


def test_a_huge_body_is_capped() -> None:
    huge = TICKET.replace("- not a list", "\n".join(["x" * 99] * 2000))
    body = pull_request_body(ticket(huge), 1, {}, {})
    assert len(body) <= BODY_MAX
    assert body.endswith("\n\n*(cut at 60,000 characters)*")


def test_section_and_fallbacks() -> None:
    assert section("## Scope\nDo it.\n## Done when\n- [ ] x\n", "scope") == "Do it."
    assert section("no headings", "Purpose") is None
    plain = ticket(TICKET.replace("## Purpose", "## Context"))
    body = pull_request_body(plain, 1, {}, {})
    assert "\n\n## Purpose\n\nIgnored when there is a purpose\\.\n\n" in body
    assert "*(no gate results)*" in body
