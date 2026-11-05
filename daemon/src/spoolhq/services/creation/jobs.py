"""The daemon's creation jobs: each runs on its own thread and is kept in memory for an
hour after it ends (DECISIONS 337)."""

import copy
import threading
import time
import uuid
from collections.abc import Callable
from pathlib import Path

from spoolhq.services.creation.job import Job, Runner
from spoolhq.services.creation.request import CreateProject, CreationError, check_request

KEEP_S = 3600.0
CANCEL_WAIT_S = 15.0


class UnknownJobError(Exception):
    pass


class CreationJobs:
    def __init__(
        self,
        *,
        projects_dir: Path,
        worktrees_dir: Path,
        home: Path,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.projects_dir, self.worktrees_dir, self.home = projects_dir, worktrees_dir, home
        self._clock = clock
        self._lock = threading.Lock()
        self._jobs: dict[str, tuple[Job, threading.Event, threading.Thread]] = {}

    def _prune(self) -> None:
        now = self._clock()
        for job_id, (job, _, _) in list(self._jobs.items()):
            if job.ended_at is not None and now - job.ended_at > KEEP_S:
                del self._jobs[job_id]

    def start(self, request: CreateProject) -> Job:
        """Check ``request`` (CreationError before anything starts) and start its job."""
        checked = check_request(
            request,
            projects_dir=self.projects_dir,
            worktrees_dir=self.worktrees_dir,
            home=self.home,
        )
        with self._lock:
            self._prune()
            if any(
                job.project == request.name and job.state == "running"
                for job, _, _ in self._jobs.values()
            ):
                raise CreationError("name", "A project with this name is being created")
            job = Job(id=uuid.uuid4().hex, project=request.name, source=request.source)
            cancel = threading.Event()
            runner = Runner(
                job, checked, projects_dir=self.projects_dir, cancel=cancel, lock=self._lock
            )
            thread = threading.Thread(target=runner.run, name=f"create-{job.id}", daemon=True)
            self._jobs[job.id] = (job, cancel, thread)
            thread.start()
            return copy.deepcopy(job)

    def get(self, job_id: str) -> Job:
        """A copy of the job as it is now."""
        with self._lock:
            self._prune()
            found = self._jobs.get(job_id)
            if found is None:
                raise UnknownJobError(f"no job {job_id!r}")
            return copy.deepcopy(found[0])

    def wait(self, job_id: str, timeout: float | None = None) -> Job:
        with self._lock:
            found = self._jobs.get(job_id)
        if found is None:
            raise UnknownJobError(f"no job {job_id!r}")
        found[2].join(timeout)
        return self.get(job_id)

    def cancel(self, job_id: str) -> Job:
        """Stop the job and wait (up to 15 s) for its rollback; a job that ended stays."""
        with self._lock:
            found = self._jobs.get(job_id)
            if found is None:
                raise UnknownJobError(f"no job {job_id!r}")
            found[1].set()
        return self.wait(job_id, CANCEL_WAIT_S)

    def close(self) -> None:
        """Cancel every running job and wait for its rollback."""
        with self._lock:
            running = [job.id for job, _, _ in self._jobs.values() if job.state == "running"]
        for job_id in running:
            self.cancel(job_id)
