"""A pull request's title and body: the ticket's title and purpose, the reviewer's verdict on each
"Done when" item, the gate results and the run id.

Ticket and agent text is untrusted, so every piece of it is escaped: markdown and HTML
show as text, and nobody gets mentioned. The body is capped at 60,000 characters.
"""

import re
from typing import Any

from spoolhq.services.git import commit_message
from spoolhq.services.tickets import Ticket

BODY_MAX = 60_000
CUT_NOTE = "\n\n*(cut at 60,000 characters)*"
_SPECIAL_RE = re.compile(r"([\\`*_{}\[\]()#+\-.!|~=])")
_SECTION_RE = re.compile(r"^##[ \t]+(.+?)[ \t]*$", re.MULTILINE)


def md_escape(text: str) -> str:
    """``text`` as literal markdown: specials backslash-escaped, ``& < >`` and ``@`` as
    HTML entities (so no tag renders and no ``@user`` is notified)."""
    text = _SPECIAL_RE.sub(r"\\\1", text.replace("\r\n", "\n"))
    for char, entity in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ("@", "&#64;")):
        text = text.replace(char, entity)
    return text


def pull_request_title(ticket: Ticket) -> str:
    """``<id>: <title>``, one line, as the squash commit's subject."""
    return commit_message(ticket.id, ticket.meta.title, None, 0).split("\n", 1)[0]


def section(body: str, name: str) -> str | None:
    """The text under ``## <name>`` up to the next ``## `` heading, if any."""
    headings = list(_SECTION_RE.finditer(body))
    for index, heading in enumerate(headings):
        if heading.group(1).strip().lower() == name.lower():
            end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
            return body[heading.end() : end].strip() or None
    return None


def _done_when(ticket: Ticket, review: dict[str, Any]) -> list[str]:
    verdicts = {item.get("index"): item for item in review.get("items", [])}
    lines = []
    for index, item in enumerate(ticket.done_when, start=1):
        verdict = verdicts.get(index)
        if verdict is None:
            lines.append(f"- ➖ no verdict: {md_escape(item.text)}")
            continue
        mark = "✅ met" if verdict.get("met") else "❌ not met"
        reason = str(verdict.get("reason") or "")
        lines.append(
            f"- {mark}: {md_escape(item.text)}" + (f" — {md_escape(reason)}" if reason else "")
        )
    return lines or ["*(none)*"]


def _gates(gates: dict[str, Any]) -> list[str]:
    rows = ["| Command | Result | Time |", "| --- | --- | --- |"]
    for result in gates.get("results", []):
        status = "✅ pass" if result.get("status") == "passed" else f"❌ {result.get('status')}"
        seconds = float(result.get("duration_s") or 0)
        rows.append(f"| {md_escape(str(result.get('command', '')))} | {status} | {seconds:.1f} s |")
    return rows if len(rows) > 2 else ["*(no gate results)*"]


def pull_request_body(
    ticket: Ticket, run_id: int, review: dict[str, Any], gates: dict[str, Any]
) -> str:
    """The body from the approved attempt's ``review.json`` and ``gates.json``."""
    purpose = section(ticket.body, "Purpose") or section(ticket.body, "Scope")
    parts = [
        md_escape(pull_request_title(ticket)),
        f"## Purpose\n\n{md_escape(purpose)}" if purpose else "",
        "## Done when\n\n" + "\n".join(_done_when(ticket, review)),
        "## Gates\n\n" + "\n".join(_gates(gates)),
        f"SpoolHQ run {run_id} · ticket {md_escape(ticket.id)}",
    ]
    body = "\n\n".join(part for part in parts if part)
    if len(body) <= BODY_MAX:
        return body
    # Cut on a line, and never inside an escape or an entity.
    cut = body[: BODY_MAX - len(CUT_NOTE)].rsplit("\n", 1)[0]
    return cut + CUT_NOTE
