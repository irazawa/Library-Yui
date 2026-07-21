"""In-memory job store for download jobs.

Jobs are keyed by a UUID string and hold their source URL plus a simple
lifecycle status. In addition to the in-memory store (the source of truth
for the API), created/updated jobs are dual-written best-effort into the
SQLite ``jobs`` table managed by :mod:`app.database`, so they survive
process restarts once a future task wires a read-back path. Any database
error is swallowed so the in-memory store is never affected.
"""

from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import TypedDict

from app.database import DEFAULT_DB_PATH, get_connection, init_db

logger = logging.getLogger(__name__)


class JobRecord(TypedDict):
    id: str
    url: str
    status: str
    mode: str


# Module-level store shared across requests within the same process.
_JOBS: dict[str, JobRecord] = {}

# Side-table of ISO-8601 (UTC) timestamps keyed by job id. Kept separate
# from :class:`JobRecord` so the API response shape (id/url/status/mode)
# stays stable; these are used only for best-effort SQLite persistence.
_JOB_TIMESTAMPS: dict[str, dict[str, str]] = {}


# Allowed download modes. ``audio`` extracts an MP3; ``video`` downloads an
# MP4. Defaults to ``audio`` to preserve the legacy downloader behavior.
ALLOWED_MODES = ("audio", "video")
DEFAULT_MODE = "audio"

# SQLite database path used for best-effort job persistence. Defaults to the
# shared Library-Yui database; tests override it via :func:`set_jobs_db_path`.
_jobs_db_path = DEFAULT_DB_PATH


def set_jobs_db_path(path: object) -> None:
    """Override the database path used for job persistence (intended for tests)."""

    global _jobs_db_path
    _jobs_db_path = path


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""

    return datetime.now(timezone.utc).isoformat()


def _persist_job(job: JobRecord, created_at: str, updated_at: str) -> None:
    """Best-effort upsert of *job* into the SQLite ``jobs`` table.

    Any database error is logged and swallowed so the in-memory store — the
    source of truth for the API — is never affected. The ``jobs`` table is
    created lazily via :func:`init_db` on the configured database path. On
    conflict (status update) only ``url``/``mode``/``status``/``updated_at``
    are refreshed, leaving the original ``created_at`` intact.
    """

    try:
        init_db(_jobs_db_path)
        connection = get_connection(_jobs_db_path)
        try:
            connection.execute(
                "INSERT INTO jobs (id, url, mode, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "url=excluded.url, mode=excluded.mode, "
                "status=excluded.status, updated_at=excluded.updated_at",
                (job["id"], job["url"], job["mode"], job["status"], created_at, updated_at),
            )
            connection.commit()
        finally:
            connection.close()
    except sqlite3.Error as exc:
        logger.warning("Job persistence failed for %s: %s", job["id"], exc)
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error persisting job %s", job["id"])


def create_job(url: str, mode: str = DEFAULT_MODE) -> JobRecord:
    """Create a new pending download job for the given URL.

    *mode* selects the download format (``audio`` for MP3, ``video`` for
    MP4) and defaults to ``audio`` to match the legacy downloader. The
    caller is expected to have validated *mode* (e.g. via the API request
    model); an unknown value is still stored verbatim rather than rejected
    here so the store stays a dumb data layer.
    """

    job_id = uuid.uuid4().hex
    now = _now_iso()
    job: JobRecord = {"id": job_id, "url": url, "status": "pending", "mode": mode}
    _JOBS[job_id] = job
    _JOB_TIMESTAMPS[job_id] = {"created_at": now, "updated_at": now}
    _persist_job(job, now, now)
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
    ts = _JOB_TIMESTAMPS.get(job_id)
    created_at = ts["created_at"] if ts else _now_iso()
    updated_at = _now_iso()
    _JOB_TIMESTAMPS[job_id] = {"created_at": created_at, "updated_at": updated_at}
    _persist_job(job, created_at, updated_at)
    return job


def _unpersist_job(job_id: str) -> None:
    """Best-effort removal of *job_id* from the SQLite ``jobs`` table.

    Mirrors :func:`_persist_job`: any database error is logged and swallowed
    so the in-memory store — the source of truth for the API — is never
    affected. A missing ``jobs`` table (e.g. a fresh DB that never had a job
    written) is treated as a no-op rather than an error.
    """

    try:
        connection = get_connection(_jobs_db_path)
        try:
            connection.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            connection.commit()
        finally:
            connection.close()
    except sqlite3.Error as exc:
        # A missing ``jobs`` table means there is nothing to delete; treat
        # that case as a quiet no-op instead of a noisy warning.
        if "no such table" in str(exc).lower():
            return
        logger.warning("Job unpersist failed for %s: %s", job_id, exc)
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error unpersisting job %s", job_id)


def delete_job(job_id: str) -> bool:
    """Remove a job by id from the in-memory store.

    Returns ``True`` when a job was removed, or ``False`` when the job did
    not exist. The SQLite ``jobs`` row (if any) is removed best-effort via
    :func:`_unpersist_job`; any database failure is swallowed so the
    in-memory removal still succeeds.
    """

    existed = _JOBS.pop(job_id, None) is not None
    _JOB_TIMESTAMPS.pop(job_id, None)
    if existed:
        _unpersist_job(job_id)
    return existed


def reset_jobs() -> None:
    """Clear all jobs. Intended for tests."""

    _JOBS.clear()
    _JOB_TIMESTAMPS.clear()
