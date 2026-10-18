"""The daemon's single-instance lock: ``~/.spoolhq/daemon.lock``.

``spool serve`` holds it for the daemon's lifetime, so crash recovery never runs while
another daemon still has live runs. It is an OS lock (``fcntl.flock`` on POSIX,
``msvcrt.locking`` on Windows), released by the OS when the process dies, so a crashed
daemon never leaves a stale lock. The holder's pid is written into the file for the
error message.
"""

import os
import sys
from pathlib import Path
from types import TracebackType
from typing import Self

LOCK_FILE = "daemon.lock"

# Windows locks are mandatory byte ranges: lock one byte far past the pid, so another
# process can still read the pid. POSIX flock locks the whole file regardless.
_LOCK_OFFSET = 1 << 20
_PID_READ_BYTES = 64


class DaemonAlreadyRunning(Exception):
    def __init__(self, pid: int | None) -> None:
        self.pid = pid
        holder = f"pid {pid}" if pid is not None else "pid unknown"
        super().__init__(f"another SpoolHQ daemon is already running ({holder})")


def lock_path(home: Path) -> Path:
    return home / LOCK_FILE


if sys.platform == "win32":
    import msvcrt

    def _try_lock(fd: int) -> None:
        os.lseek(fd, _LOCK_OFFSET, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)

    def _unlock(fd: int) -> None:
        os.lseek(fd, _LOCK_OFFSET, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _try_lock(fd: int) -> None:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock(fd: int) -> None:
        fcntl.flock(fd, fcntl.LOCK_UN)


def _read_pid(fd: int) -> int | None:
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        text = os.read(fd, _PID_READ_BYTES).decode("ascii").strip()
        pid = int(text)
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    return pid if pid > 0 else None


class DaemonLock:
    """A held lock; ``release`` (or leaving the ``with`` block) frees it."""

    def __init__(self, path: Path, fd: int) -> None:
        self.path = path
        self._fd: int | None = fd

    @property
    def held(self) -> bool:
        return self._fd is not None

    def release(self) -> None:
        fd, self._fd = self._fd, None
        if fd is None:
            return
        try:
            _unlock(fd)
        finally:
            os.close(fd)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.release()


def acquire_daemon_lock(home: Path) -> DaemonLock:
    """Take the lock in ``home`` and write this process's pid into it.

    Raises DaemonAlreadyRunning, with the holder's pid when the file has one, if
    another process (or another ``acquire_daemon_lock`` in this one) holds it.
    """
    path = lock_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    # O_BINARY: no newline translation on Windows.
    fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_BINARY", 0), 0o600)
    try:
        _try_lock(fd)
    except OSError:
        pid = _read_pid(fd)
        os.close(fd)
        raise DaemonAlreadyRunning(pid) from None
    try:
        data = f"{os.getpid()}\n".encode("ascii")
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, data)
        os.ftruncate(fd, len(data))
    except BaseException:
        _unlock(fd)
        os.close(fd)
        raise
    return DaemonLock(path, fd)
