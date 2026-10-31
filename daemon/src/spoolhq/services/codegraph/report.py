"""The part of ``GRAPH_REPORT.md`` that goes into a prompt.

Kept: the summary, the most connected nodes, surprising connections, import cycles and
the communities (each a ``### `` section with ``Nodes (N)``). Left out: the run's own
folder name in the title, the build commit, the navigation list of placeholder names,
knowledge gaps and suggested questions, which tell the reader to run Graphify.
"""

KEPT_SECTIONS = ("Summary", "God Nodes", "Surprising Connections", "Import Cycles", "Communities")
_SECTION = "## "


def summary(report: str) -> str:
    """The kept ``## `` sections of ``report``, in order."""
    sections: list[list[str]] = []
    for line in report.replace("\r\n", "\n").split("\n"):
        if line.startswith(_SECTION):
            sections.append([line])
        elif sections:
            sections[-1].append(line)
    kept = [s for s in sections if s[0][len(_SECTION) :].startswith(KEPT_SECTIONS)]
    return "\n\n".join("\n".join(s).strip("\n") for s in kept) + "\n" if kept else ""
