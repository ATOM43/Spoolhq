"""Agent policy constants shared by ``services/agents``, ``services/context`` and
``services/gates``.

They live in ``core`` because those packages must not import another service.
"""

from collections.abc import Collection, Mapping

# The git commands an agent may run: they read the repository and change nothing.
READ_ONLY_GIT: tuple[str, ...] = ("git status", "git diff", "git log", "git show")

# The environment variables a child process (the agent, a gate) may inherit.
ENV_ALLOWED = frozenset(
    {
        "PATH",
        "HOME",
        "USER",
        "LOGNAME",
        "LANG",
        "TMPDIR",
        "TMP",
        "TEMP",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "XDG_CACHE_HOME",
        "XDG_RUNTIME_DIR",
        "DBUS_SESSION_BUS_ADDRESS",
        "CLAUDE_CONFIG_DIR",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "NO_PROXY",
        "https_proxy",
        "http_proxy",
        "no_proxy",
        # A corporate proxy's CA, so Claude Code can reach the API through it.
        "NODE_EXTRA_CA_CERTS",
        "SSL_CERT_FILE",
    }
)
ENV_ALLOWED_WINDOWS = frozenset(
    {"SYSTEMROOT", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "COMSPEC", "PATHEXT"}
)
ENV_ALLOWED_PREFIXES = ("LC_",)


def allowed_env(
    parent: Mapping[str, str], *, platform: str, extra: Collection[str] = ()
) -> dict[str, str]:
    """The variables of ``parent`` on the allowlist (plus ``extra``), nothing else."""
    windows = platform == "win32"
    allowed = ENV_ALLOWED | ENV_ALLOWED_WINDOWS if windows else ENV_ALLOWED
    env: dict[str, str] = {}
    for name, value in parent.items():
        key = name.upper() if windows else name  # Windows names ignore case
        if key in allowed or key in extra or key.startswith(ENV_ALLOWED_PREFIXES):
            env[name] = value
    return env
