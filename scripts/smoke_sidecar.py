"""Smoke-test a built sidecar binary (docs/packaging.md); CI's package workflow runs it.

`python scripts/smoke_sidecar.py <binary>`: everything runs on a temp home, a temp
projects folder and a free port, so a daemon you have running is never touched.
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

TIMEOUT_S = 30
CHECK = "git --version"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def run(binary: str, *args: str, env: dict[str, str], ok: bool = True) -> str:
    done = subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [binary, *args], env=env, capture_output=True, encoding="utf-8", timeout=120
    )
    output = done.stdout + done.stderr
    if ok and done.returncode != 0:
        sys.exit(f"FAIL spool {' '.join(args)} exited {done.returncode}:\n{output}")
    print(f"ok   spool {' '.join(args)}")
    return output


def get(port: int, path: str, token: str) -> object:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(  # noqa: S310 - fixed http://127.0.0.1 URL
        f"http://127.0.0.1:{port}{path}", headers={"Authorization": f"Bearer {token}"}
    )
    with opener.open(request, timeout=5) as response:
        return json.loads(response.read())


def wait_for_health(port: int, home: Path, server: subprocess.Popen[str]) -> str:
    deadline = time.monotonic() + TIMEOUT_S
    while time.monotonic() < deadline:
        if server.poll() is not None:
            sys.exit(f"FAIL serve exited {server.returncode}:\n{server.communicate()[0]}")
        try:
            token = (home / "token").read_text("utf-8").strip()
            health = get(port, "/api/health", token)
            get(port, "/api/version", token)
            print(f"ok   GET /api/health with the token: {health}")
            return token
        except (OSError, ValueError):
            time.sleep(0.5)
    sys.exit(f"FAIL no health on port {port} within {TIMEOUT_S} s")


def main() -> None:
    binary = str(Path(sys.argv[1]).resolve())
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        port = free_port()
        env = {
            **os.environ,
            "SPOOLHQ_HOME": str(root / "home"),
            "SPOOLHQ_PROJECTS_DIR": str(root / "projects"),
            "SPOOLHQ_PORT": str(port),
            # CI runners have no git identity for the initial commit.
            "GIT_AUTHOR_NAME": "smoke",
            "GIT_AUTHOR_EMAIL": "smoke@example.invalid",
            "GIT_COMMITTER_NAME": "smoke",
            "GIT_COMMITTER_EMAIL": "smoke@example.invalid",
        }
        env.pop("SPOOLHQ_DEV_FAKE_RUNNER", None)

        if "spool " not in run(binary, "version", env=env):
            sys.exit("FAIL version printed no `spool <version>`")
        refused = run(binary, "serve", env={**env, "SPOOLHQ_DEV_FAKE_RUNNER": "happy"}, ok=False)
        if "for development only" not in refused:
            sys.exit(f"FAIL the fake runner was not refused:\n{refused}")
        print("ok   SPOOLHQ_DEV_FAKE_RUNNER refused")

        server = subprocess.Popen(  # noqa: S603 - fixed argument list, no shell
            [binary, "serve"], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        try:
            wait_for_health(port, root / "home", server)
            run(
                binary, "init", "empty", "--source", "empty", "--repo", str(root / "empty"), env=env
            )
            commands = ["--install", CHECK, "--lint", CHECK, "--test", CHECK]
            repo = str(root / "tpl")
            run(
                binary,
                "init",
                "tpl",
                "--template",
                "fastapi-react",
                "--repo",
                repo,
                *commands,
                env=env,
            )
            scope = root / "scope.md"
            scope.write_text("Smoke test.\n", "utf-8")
            ticket = ["--title", "Smoke", "--done-when", "Works", "--scope-file", str(scope)]
            run(binary, "tickets", "new", "empty", *ticket, env=env)
            if "implementing one ticket" not in run(
                binary, "prompt", "show", "empty", "T01", env=env
            ):
                sys.exit("FAIL the implementer prompt did not render")
        finally:
            server.terminate()
            server.wait(timeout=TIMEOUT_S)
    print("smoke test passed")


if __name__ == "__main__":
    main()
