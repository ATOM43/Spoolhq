"""Start the real daemon in a subprocess and talk to it over HTTP."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from spoolhq.core.auth import read_token

pytestmark = pytest.mark.integration

STARTUP_TIMEOUT_S = 30.0


def wait_for_health(base_url: str, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_S
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail(f"daemon exited early with code {process.returncode}")
        try:
            response = httpx.get(f"{base_url}/api/health", timeout=1.0, trust_env=False)
        except httpx.TransportError:
            time.sleep(0.2)
            continue
        assert response.json() == {"status": "ok"}
        return
    pytest.fail("daemon did not answer /api/health in time")


def test_serve_starts_and_serves_docs(home: Path, free_port: int, tmp_path: Path) -> None:
    base_url = f"http://127.0.0.1:{free_port}"
    output = tmp_path / "serve-output.txt"
    with output.open("wb") as out:
        process = subprocess.Popen(  # noqa: S603 - fixed argument list, no shell
            [sys.executable, "-m", "spoolhq", "serve", "--port", str(free_port)],
            stdout=out,
            stderr=subprocess.STDOUT,
            env=os.environ.copy(),
        )
        try:
            wait_for_health(base_url, process)
            docs = httpx.get(f"{base_url}/docs", timeout=5.0, trust_env=False)
            assert docs.status_code == 200
            token = read_token(home)
            assert token is not None
            version = httpx.get(
                f"{base_url}/api/version",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0,
                trust_env=False,
            )
            assert version.status_code == 200
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    assert f"{base_url}/docs" in output.read_text(encoding="utf-8")
    log_text = (home / "logs" / "daemon.log").read_text(encoding="utf-8")
    assert token not in log_text
    loggers = {json.loads(line)["logger"] for line in log_text.splitlines()}
    assert "uvicorn.access" in loggers
