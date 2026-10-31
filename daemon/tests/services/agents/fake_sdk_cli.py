"""A stand-in for the Claude Code CLI behind the Agent SDK, run as a real subprocess.

    python fake_sdk_cli.py --scenario <jsonl> --record <json> [options] <cli args...>

``--version`` prints ``--version-string`` (default 2.1.316). Anything else is a run that
speaks the SDK's control protocol the way Claude Code 2.1.316 does: it answers the
``initialize`` request, reads the prompt, then prints the scenario's lines. Before each
``tool_use`` it asks the SDK's ``PreToolUse`` hook (a ``hook_callback`` control request)
and, if the hook denies the call, replaces the call's recorded result with the error
Claude Code sends (``PreToolUse:<tool> hook error: <reason>``); an allowed ``Write`` is
written into the cwd. ``init``'s ``apiKeySource`` is ``ANTHROPIC_API_KEY`` when that
variable is set, else ``none`` (as the real CLI reports), or ``--key-source``. It records
its argv, cwd, environment variable names, the values of ``RECORDED_VARS`` (the API key
only as a SHA-256), the prompt and the hook's answers to ``--record``, then sleeps
``--sleep`` seconds and exits with ``--exit-code``. ``--stderr`` prints a line there.
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

OPTIONS = {
    "--scenario",
    "--record",
    "--version-string",
    "--sleep",
    "--exit-code",
    "--stderr",
    "--key-source",
}
RECORDED_VARS = (
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CONFIG_DIR",
    "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB",
)


def parse(argv: list[str]) -> tuple[dict[str, str], list[str]]:
    options: dict[str, str] = {}
    rest: list[str] = []
    index = 0
    while index < len(argv):
        if argv[index] in OPTIONS:
            options[argv[index]] = argv[index + 1]
            index += 2
        else:
            rest.append(argv[index])
            index += 1
    return options, rest


def send(message: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def receive() -> dict[str, Any]:
    line = sys.stdin.readline()
    if not line:
        raise SystemExit(3)
    message: dict[str, Any] = json.loads(line)
    return message


def ask_hook(callback_id: str, block: dict[str, Any], number: int) -> dict[str, Any]:
    request_id = f"fake_hook_{number}"
    send(
        {
            "type": "control_request",
            "request_id": request_id,
            "request": {
                "subtype": "hook_callback",
                "callback_id": callback_id,
                "tool_use_id": block["id"],
                "input": {
                    "hook_event_name": "PreToolUse",
                    "session_id": "fake",
                    "transcript_path": "",
                    "cwd": os.getcwd(),
                    "tool_name": block["name"],
                    "tool_input": block["input"],
                    "tool_use_id": block["id"],
                },
            },
        }
    )
    while True:
        reply = receive()
        response = reply.get("response", {})
        if reply.get("type") == "control_response" and response.get("request_id") == request_id:
            output: dict[str, Any] = response.get("response") or {}
            return output


def write_file(block: dict[str, Any]) -> None:
    tool_input = block["input"]
    path = Path(tool_input["file_path"])
    path = path if path.is_absolute() else Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tool_input["content"], encoding="utf-8")


def run(options: dict[str, str], rest: list[str]) -> int:
    key = os.environ.get("ANTHROPIC_API_KEY")
    record: dict[str, Any] = {
        "argv": rest,
        "cwd": os.getcwd(),
        "env_names": sorted(os.environ),
        "env": {name: os.environ.get(name) for name in RECORDED_VARS},
        "api_key_sha256": hashlib.sha256(key.encode()).hexdigest() if key else None,
        "pid": os.getpid(),
        "hooks": [],
    }
    record_path = Path(options["--record"])

    def save() -> None:
        record_path.write_text(json.dumps(record), encoding="utf-8")

    save()
    init = receive()
    hooks = init["request"].get("hooks") or {}
    callback_ids = [
        cid for matcher in hooks.get("PreToolUse", []) for cid in matcher["hookCallbackIds"]
    ]
    send(
        {
            "type": "control_response",
            "response": {"subtype": "success", "request_id": init["request_id"], "response": {}},
        }
    )
    prompt = receive()
    record["stdin"] = prompt["message"]["content"]
    save()
    if "--stderr" in options:
        print(options["--stderr"], file=sys.stderr, flush=True)

    denied: dict[str, str] = {}
    lines = Path(options["--scenario"]).read_text(encoding="utf-8").splitlines()
    for line in filter(str.strip, lines):
        message = json.loads(line)
        if message.get("subtype") == "init":
            source = "ANTHROPIC_API_KEY" if key else "none"
            message["apiKeySource"] = options.get("--key-source", source)
        if message.get("type") == "user":
            for block in message.get("message", {}).get("content", []):
                reason = (
                    denied.get(block.get("tool_use_id", "")) if isinstance(block, dict) else None
                )
                if reason is not None:
                    block.update(content=reason, is_error=True)
        send(message)
        if message.get("type") != "assistant":
            continue
        for block in message.get("message", {}).get("content", []):
            if block.get("type") != "tool_use":
                continue
            for callback_id in callback_ids:
                output = ask_hook(callback_id, block, len(record["hooks"]))
                record["hooks"].append({"tool": block["name"], "output": output})
                save()
                specific = output.get("hookSpecificOutput", {})
                if specific.get("permissionDecision") == "deny":
                    reason = specific.get("permissionDecisionReason", "")
                    denied[block["id"]] = f"PreToolUse:{block['name']} hook error: {reason}"
            if block["name"] == "Write" and block["id"] not in denied:
                write_file(block)
    time.sleep(float(options.get("--sleep", "0")))
    return int(options.get("--exit-code", "0"))


def main() -> int:
    options, rest = parse(sys.argv[1:])
    if rest == ["--version"]:
        print(f"{options.get('--version-string', '2.1.316')} (Claude Code)")
        return 0
    return run(options, rest)


if __name__ == "__main__":
    sys.exit(main())
