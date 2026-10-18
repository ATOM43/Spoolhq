"""Agent policy constants shared by ``services/agents`` and ``services/context``.

They live in ``core`` because the context package must not import another service.
"""

# The git commands an agent may run: they read the repository and change nothing.
READ_ONLY_GIT: tuple[str, ...] = ("git status", "git diff", "git log", "git show")
