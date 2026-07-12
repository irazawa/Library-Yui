import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl

from app.downloader import download_mp3, is_downloads_enabled
from app.jobs import create_job, get_job, list_jobs, update_job_status

logger = logging.getLogger(__name__)

router = APIRouter(tags=["jobs"])


class JobCreateRequest(BaseModel):
    url: HttpUrl


class JobResponse(BaseModel):
    id: str
    url: str
    status: str


class JobListResponse(BaseModel):
    items: list[JobResponse]


def _is_youtube_url(url: str) -> bool:
    """Return True when *url* points to a recognized YouTube host."""

    lowered = url.lower()
    return any(
        host in lowered
        for host in (
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "youtu.be",
            "www.youtu.be",
            "music.youtube.com",
        )
    )


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_download_job(payload: JobCreateRequest) -> JobResponse:
    """Accept a YouTube URL and initialize a pending download job.

    Non-YouTube URLs are rejected with HTTP 422.
    """

    url = str(payload.url)
    if not _is_youtube_url(url):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only YouTube URLs are accepted",
        )

    job = create_job(url)
    return JobResponse(**job)


@router.get("/jobs", response_model=JobListResponse)
def list_download_jobs() -> JobListResponse:
    """Return all jobs (id, url, status) from the in-memory store.

    Jobs are returned in creation order. The response shape is
    ``{"items": [...]}`` mirroring the other collection endpoints.
    """

    return JobListResponse(items=[JobResponse(**job) for job in list_jobs()])


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_download_job(job_id: str) -> JobResponse:
    """Return the current status of a specific download job."""

    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse(**job)


@router.post("/jobs/{job_id}/start", response_model=JobResponse)
def start_download_job(job_id: str) -> JobResponse:
    """Transition a job from ``pending`` to ``downloading``.

    When the real-download feature flag (``LIBRARY_YUI_DOWNLOADS_ENABLED``) is
    enabled, this endpoint also runs the MP3 download synchronously and
    transitions the job to ``completed`` (or ``failed``) accordingly. When the
    flag is disabled this behaves as a stub: it only flips the status to
    ``downloading`` and performs no real download, so callers remain
    idempotent. Unknown job ids return 404.
    """

    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job["status"] == "pending":
        updated = update_job_status(job_id, "downloading")
        if updated is not None:
            return _maybe_run_download(job_id) or JobResponse(**updated)
    return JobResponse(**job)


def _maybe_run_download(job_id: str) -> JobResponse | None:
    """Run the real MP3 download for *job_id* when the flag is enabled.

    Returns the updated :class:`JobResponse` when a download was attempted
    (regardless of success/failure), or ``None`` when the flag is disabled so
    the caller can fall back to the plain ``downloading`` response.
    """

    if not is_downloads_enabled():
        return None

    job = get_job(job_id)
    if job is None:
        return None

    url = job["url"]
    try:
        result = download_mp3(url)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Download failed for job %s", job_id)
        updated = update_job_status(job_id, "failed")
        if updated is not None:
            return JobResponse(**updated)
        raise

    if result["ok"]:
        updated = update_job_status(job_id, "completed")
    else:
        logger.warning(
            "Download returned non-zero exit code %s for job %s",
            result.get("returncode"),
            job_id,
        )
        updated = update_job_status(job_id, "failed")

    if updated is not None:
        return JobResponse(**updated)
    return None


@router.post("/jobs/{job_id}/complete", response_model=JobResponse)
def complete_download_job(job_id: str) -> JobResponse:
    """Transition a job to ``completed``.

    This is a stub endpoint: no file is produced yet. A job that is already
    ``completed`` is left untouched and returned as-is so callers remain
    idempotent. A job in a terminal ``failed`` state is also left untouched.
    Unknown job ids return 404.
    """

    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job["status"] in ("pending", "downloading"):
        updated = update_job_status(job_id, "completed")
        if updated is not None:
            return JobResponse(**updated)
    return JobResponse(**job)
