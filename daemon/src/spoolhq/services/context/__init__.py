"""Context: the prompt an agent starts with, and the progress note it hands back.

``build_implementer_prompt`` renders the implementer's prompt (the ticket, the relevant
part of the spec, the repository's notes and, on a retry, what went wrong) from a
sandboxed Jinja2 template, within a character budget. ``extract_progress_note`` reads
the agent's ``<progress>`` block from its final message. This package imports no
other service package; callers pass plain values in. See ``docs/context.md``.
"""

from spoolhq.core.agent_policy import READ_ONLY_GIT
from spoolhq.services.context.errors import (
    ContextBudgetError,
    ContextError,
    PromptTemplateError,
)
from spoolhq.services.context.model import (
    ATTEMPT_KINDS,
    DEFAULT_MAX_CHARS,
    ContextInputs,
    DependencyView,
    GateFailure,
    PreviousAttempt,
    RenderedPrompt,
    RepoDocs,
    ReviewNote,
    TicketView,
)
from spoolhq.services.context.progress import extract_progress_note, format_progress_entry
from spoolhq.services.context.render import (
    IMPLEMENTER_TEMPLATE,
    build_implementer_prompt,
    escape_closing_tag,
    render_template,
)

__all__ = [
    "ATTEMPT_KINDS",
    "DEFAULT_MAX_CHARS",
    "IMPLEMENTER_TEMPLATE",
    "READ_ONLY_GIT",
    "ContextBudgetError",
    "ContextError",
    "ContextInputs",
    "DependencyView",
    "GateFailure",
    "PreviousAttempt",
    "PromptTemplateError",
    "RenderedPrompt",
    "RepoDocs",
    "ReviewNote",
    "TicketView",
    "build_implementer_prompt",
    "escape_closing_tag",
    "extract_progress_note",
    "format_progress_entry",
    "render_template",
]
