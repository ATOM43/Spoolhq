"""Launch test of the built desktop app (docs/packaging.md); the release workflow runs it.

`python scripts/smoke_app.py <app executable>`: the AppImage on Linux (run under
`xvfb-run` and `dbus-run-session`), the installed `.exe` on Windows, the binary inside
the mounted `.dmg`'s `SpoolHQ.app` on macOS. The app runs on a temp home, a temp
projects folder and a free port, so a daemon or config you have is never touched.

Pass: within 60 s the app's own daemon answers `GET /api/health` as SpoolHQ, and the
app is still running 10 s later. Then `POST /api/shutdown`, stop the app, and no new
SpoolHQ process may be left after 15 s.
"""

import csv
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import IO, Protocol

HEALTH_TIMEOUT_S = 60.0
ALIVE_S = 10.0
CLEANUP_TIMEOUT_S = 15.0
POLL_S = 0.5


class SmokeError(Exception):
    pass


class App(Protocol):
    def poll(self) -> int | None: ...


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request(port: int, method: str, path: str, token: str) -> object:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(  # noqa: S310 - fixed http://127.0.0.1 URL
        f"http://127.0.0.1:{port}{path}",
        method=method,
        headers={"Authorization": f"Bearer {token}"},
    )
    with opener.open(req, timeout=5) as response:
        return json.loads(response.read())


def check_running(app: App, output: Callable[[], str]) -> None:
    if "panicked" in output():
        raise SmokeError("the app panicked")
    code = app.poll()
    if code is not None:
        raise SmokeError(f"the app exited early with code {code}")


def wait_for_health(
    app: App,
    output: Callable[[], str],
    health: Callable[[], object],
    timeout: float = HEALTH_TIMEOUT_S,
) -> None:
    """Until `health()` answers; it raises OSError or ValueError while nothing does."""
    deadline = time.monotonic() + timeout
    while True:
        check_running(app, output)
        try:
            answer = health()
        except (OSError, ValueError):
            if time.monotonic() >= deadline:
                raise SmokeError(f"no answer from GET /api/health within {timeout:g} s") from None
            time.sleep(POLL_S)
            continue
        service = answer.get("service") if isinstance(answer, dict) else None
        if service != "spoolhq":
            raise SmokeError(f'GET /api/health answered service {service!r}, not "spoolhq"')
        print(f"ok   GET /api/health: {answer}")
        return


def stay_alive(app: App, output: Callable[[], str], seconds: float = ALIVE_S) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        check_running(app, output)
        time.sleep(POLL_S)
    check_running(app, output)
    print(f"ok   the app is still running after {seconds:g} s")


def spoolhq_processes() -> dict[int, str]:
    """Running processes whose executable name contains "spoolhq", by pid."""
    if sys.platform == "win32":
        listing = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],  # noqa: S607 - the OS's own tool
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        ).stdout
        rows = [(row[1], row[0]) for row in csv.reader(listing.splitlines()) if len(row) > 1]
    else:
        listing = subprocess.run(
            ["ps", "-A", "-o", "pid=,comm="],  # noqa: S607 - the OS's own tool
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        ).stdout
        rows = [(line.split(None, 1) + [""])[:2] for line in listing.splitlines()]
    found = {}
    for pid, name in rows:
        base = Path(name.strip()).name  # macOS gives the full path
        if "spoolhq" in base.lower() and pid.isdigit():
            found[int(pid)] = base
    return found


def wait_for_cleanup(
    before: set[int],
    processes: Callable[[], dict[int, str]] = spoolhq_processes,
    timeout: float = CLEANUP_TIMEOUT_S,
) -> None:
    """No SpoolHQ process other than those in `before` may be left after `timeout`."""
    deadline = time.monotonic() + timeout
    while True:
        left = {pid: name for pid, name in processes().items() if pid not in before}
        if not left:
            print("ok   no SpoolHQ process left")
            return
        if time.monotonic() >= deadline:
            names = ", ".join(f"{name} ({pid})" for pid, name in sorted(left.items()))
            raise SmokeError(f"SpoolHQ processes still running after {timeout:g} s: {names}")
        time.sleep(POLL_S)


def launch_command(app: str) -> list[str]:
    if sys.platform.startswith("linux"):
        return ["xvfb-run", "-a", "dbus-run-session", "--", app]
    return [app]


def stop(app: subprocess.Popen[bytes]) -> None:
    """Stop the app, not the daemon: that has its own process group or Job Object."""
    if app.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(  # noqa: S603 - fixed argument list, no shell
            ["taskkill", "/F", "/PID", str(app.pid)],  # noqa: S607 - the OS's own tool
            capture_output=True,
            check=False,
        )
    else:
        # The app's session: xvfb-run, Xvfb, dbus and the app itself.
        os.killpg(app.pid, signal.SIGTERM)
        try:
            app.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(app.pid, signal.SIGKILL)
    app.wait(timeout=30)


def read(path: Path) -> str:
    return path.read_text("utf-8", errors="replace") if path.exists() else "(none)"


def run(app_path: str, root: Path, log: IO[bytes]) -> None:
    home = root / "home"
    port = free_port()
    env = {
        **os.environ,
        "SPOOLHQ_HOME": str(home),
        "SPOOLHQ_PROJECTS_DIR": str(root / "projects"),
        "SPOOLHQ_PORT": str(port),
        "APPIMAGE_EXTRACT_AND_RUN": "1",
    }
    output_path = Path(log.name)

    def output() -> str:
        return read(output_path)

    def token() -> str:
        return (home / "token").read_text("utf-8").strip()

    before = set(spoolhq_processes())
    app = subprocess.Popen(  # noqa: S603 - fixed argument list, no shell
        launch_command(app_path),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=sys.platform != "win32",
    )
    try:
        wait_for_health(app, output, lambda: request(port, "GET", "/api/health", token()))
        stay_alive(app, output)
        request(port, "POST", "/api/shutdown", token())
        print("ok   POST /api/shutdown")
    finally:
        stop(app)
    wait_for_cleanup(before)
    if "panicked" in output():
        raise SmokeError("the app panicked while quitting")


def main(argv: list[str]) -> int:
    app_path = str(Path(argv[0]).resolve())
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        output_path = root / "app-output.txt"
        try:
            with output_path.open("wb") as log:
                run(app_path, root, log)
        except (SmokeError, OSError, subprocess.SubprocessError) as err:
            print(f"FAIL {err}", file=sys.stderr)
            print(f"--- app output ---\n{read(output_path)}", file=sys.stderr)
            daemon_log = read(root / "home" / "logs" / "daemon.log")
            print(f"--- daemon log ---\n{daemon_log}", file=sys.stderr)
            return 1
    print("app launch test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
