"""Errors raised while building a prompt."""


class ContextError(Exception):
    """A prompt could not be built; the message is one line meant for the user."""


class ContextBudgetError(ContextError):
    """The prompt cannot fit in ``context.max_chars``."""


class PromptTemplateError(ContextError):
    """A prompt template is invalid: undefined variable, syntax error or sandbox violation."""
