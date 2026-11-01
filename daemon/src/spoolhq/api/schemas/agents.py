"""Response models of ``GET /api/agents``: what ``spool agents`` shows."""

from pydantic import BaseModel

from spoolhq.services.agents import BackendInfo
from spoolhq.services.codegraph import Graphify


class BackendView(BaseModel):
    name: str
    installed: bool
    version: str | None
    logged_in: bool
    auth_method: str | None
    billing: str
    policy_enforceable: bool
    reason: str | None
    policy_parts: dict[str, dict[str, bool]]
    usable: bool

    @classmethod
    def of(cls, info: BackendInfo) -> "BackendView":
        return cls(
            name=info.name,
            installed=info.installed,
            version=info.version,
            logged_in=info.logged_in,
            auth_method=info.auth_method,
            billing=str(info.billing),
            policy_enforceable=info.policy_enforceable,
            reason=info.reason,
            policy_parts={role: dict(parts) for role, parts in info.policy_parts.items()},
            usable=info.usable,
        )


class GraphifyView(BaseModel):
    installed: bool
    version: str | None
    tested: bool

    @classmethod
    def of(cls, graphify: Graphify | None) -> "GraphifyView":
        if graphify is None:
            return cls(installed=False, version=None, tested=False)
        return cls(installed=True, version=graphify.version, tested=graphify.tested)


class AgentsView(BaseModel):
    backends: list[BackendView]
    graphify: GraphifyView
