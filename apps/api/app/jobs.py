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
    mode: str


# Module-level store shared across requests within the same process.
# A future iteration will replace this with durable persistence.
_JOBS: dict[str, JobRecord] = {}


# Allowed download modes. ``audio`` extracts an MP3; ``video`` downloads an
# MP4. Defaults to ``audio`` to preserve the legacy downloader behavior.
ALLOWED_MODES = ("audio", "video")
DEFAULT_MODE = "audio"


def create_job(url: str, mode: str = DEFAULT_MODE) -> JobRecord:
    """Create a new pending download job for the given URL.

    *mode* selects the download format (``audio`` for MP3, ``video`` for
    MP4) and defaults to ``audio`` to match the legacy downloader. The
    caller is expected to have validated *mode* (e.g. via the API request
    model); an unknown value is still stored verbatim rather than rejected
    here so the store stays a dumb data layer.
    """

    job_id = uuid.uuid4().hex
    job: JobRecord = {"id": job_id, "url": url, "status": "pending", "mode": mode}
    _JOBS[job_id] = job
    return job


def list_jobs() -> list[JobRecord]:
    """Return all jobs in insertion order.

    The list reflects the order in which jobs were created. A future
    iteration may add pagination or sorting by recency.
    """

    return list(_JOBS.values())


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
