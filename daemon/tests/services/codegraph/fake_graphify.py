"""A stand-in for Graphify 0.9.92, run as a real subprocess.

    python fake_graphify.py --state <dir> <graphify args...>

``<dir>/behaviour.json`` (optional) sets ``version`` (default 0.9.92; ``""`` prints no
version), ``fail`` (a list of ``full``, ``update`` or ``cluster``: those commands exit 1),
``sleep`` (seconds before each ``extract``) and ``report`` (the file ``cluster-only``
copies to ``GRAPH_REPORT.md``). Each call is appended to ``<dir>/calls.jsonl`` as
``{"command": "version" | "full" | "update" | "cluster", "argv": [...], "cwd": ...}``;
``extract`` with ``--force`` is a full build, without it an update. ``extract`` writes
``graphify-out/manifest.json`` (the file count) and ``graph.json`` under ``--out``.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any


def main(argv: list[str]) -> int:
    state = Path(argv[argv.index("--state") + 1])
    args = argv[argv.index("--state") + 2 :]
    behaviour_file = state / "behaviour.json"
    behaviour: dict[str, Any] = (
        json.loads(behaviour_file.read_text(encoding="utf-8")) if behaviour_file.is_file() else {}
    )
    if args == ["--version"]:
        command = "version"
    elif args[0] == "extract":
        command = "full" if "--force" in args else "update"
    else:
        command = "cluster"
    with (state / "calls.jsonl").open("a", encoding="utf-8") as calls:
        calls.write(json.dumps({"command": command, "argv": args, "cwd": os.getcwd()}) + "\n")
    if command == "version":
        version = behaviour.get("version", "0.9.92")
        print(f"graphify {version}" if version else "graphify: unknown")
        return 0
    if command in behaviour.get("fail", []):
        print(f"fake graphify: {command} failed", file=sys.stderr)
        return 1
    if command == "cluster":
        out = Path(args[1]) / "graphify-out"
        report = Path(behaviour["report"]).read_text(encoding="utf-8")
        (out / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
        return 0
    time.sleep(float(behaviour.get("sleep", 0)))
    source, out = Path(args[1]), Path(args[args.index("--out") + 1]) / "graphify-out"
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(p.name for p in source.rglob("*.py"))
    (out / "manifest.json").write_text(json.dumps({"files": files}), encoding="utf-8")
    (out / "graph.json").write_text(json.dumps({"nodes": files}), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
