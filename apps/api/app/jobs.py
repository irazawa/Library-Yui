"""In-memory job store for download jobs.

This is a minimal placeholder store so the API can create and track jobs
before a real persistence layer exists. Jobs are keyed by a UUID string and
hold their source URL plus a simple lifecycle status.
"""

from __future__ import annotations

import uuid
from typing import TypedDict


class JobRecord(TypedDict):
    id: str
    url: str
    status: str


# Module-level store shared across requests within the same process.
# A future iteration will replace this with durable persistence.
_JOBS: dict[str, JobRecord] = {}


def create_job(url: str) -> JobRecord:
    """Create a new pending download job for the given URL."""

    job_id = uuid.uuid4().hex
    job: JobRecord = {"id": job_id, "url": url, "status": "pending"}
    _JOBS[job_id] = job
    return job


def get_job(job_id: str) -> JobRecord | None:
    """Return a job by id, or ``None`` when it does not exist."""

    return _JOBS.get(job_id)


def update_job_status(job_id: str, new_status: str) -> JobRecord | None:
    """Set the status of an existing job.

    Returns the updated job record, or ``None`` when the job does not exist.
    """

    job = _JOBS.get(job_id)
    if job is None:
        return None
    job["status"] = new_status
    return job


def reset_jobs() -> None:
    """Clear all jobs. Intended for tests."""

    _JOBS.clear()
