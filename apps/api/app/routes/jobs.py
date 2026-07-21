import logging
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl

from app.downloader import (
    download_mp3,
    download_mp4,
    extract_thumbnail,
    is_downloads_enabled,
)
from app.jobs import create_job, delete_job, get_job, list_jobs, update_job_status
from app.storage import VIDEO_DIR

logger = logging.getLogger(__name__)

router = APIRouter()


class JobCreateRequest(BaseModel):
    url: HttpUrl
    # Optional download format. ``audio`` (default) extracts an MP3; ``video``
    # downloads an MP4. Unknown values are rejected by Pydantic with HTTP 422.
    mode: Literal["audio", "video"] = "audio"


class JobResponse(BaseModel):
    id: str
    url: str
    status: str
    mode: str


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


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED, tags=["Jobs"])
def create_download_job(payload: JobCreateRequest) -> JobResponse:
    """Accept a YouTube URL and initialize a pending download job.

    Non-YouTube URLs are rejected with HTTP 422. The optional ``mode`` field
    selects the download format (``audio`` or ``video``); unknown values are
    rejected by the request model with HTTP 422.
    """

    url = str(payload.url)
    if not _is_youtube_url(url):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only YouTube URLs are accepted",
        )

    job = create_job(url, mode=payload.mode)
    return JobResponse(**job)


@router.get("/jobs", response_model=JobListResponse, tags=["Jobs"])
def list_download_jobs() -> JobListResponse:
    """Return all jobs (id, url, status) from the in-memory store.

    Jobs are returned in creation order. The response shape is
    ``{"items": [...]}`` mirroring the other collection endpoints.
    """

    return JobListResponse(items=[JobResponse(**job) for job in list_jobs()])


@router.get("/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
def get_download_job(job_id: str) -> JobResponse:
    """Return the current status of a specific download job."""

    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse(**job)


@router.post("/jobs/{job_id}/start", response_model=JobResponse, tags=["Jobs"])
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
    """Run the real download for *job_id* when the flag is enabled.

    Returns the updated :class:`JobResponse` when a download was attempted
    (regardless of success/failure), or ``None`` when the flag is disabled so
    the caller can fall back to the plain ``downloading`` response.

    The download function is chosen based on the job ``mode``: ``video``
    invokes :func:`download_mp4` (MP4 into ``library/video``); any other
    value (including the default ``audio``) invokes :func:`download_mp3`.
    """

    if not is_downloads_enabled():
        return None

    job = get_job(job_id)
    if job is None:
        return None

    url = job["url"]
    mode = job.get("mode", "audio")
    download_fn = download_mp4 if mode == "video" else download_mp3

    try:
        result = download_fn(url)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Download failed for job %s", job_id)
        updated = update_job_status(job_id, "failed")
        if updated is not None:
            return JobResponse(**updated)
        raise

    if result["ok"]:
        updated = update_job_status(job_id, "completed")
        # For a successful video download, also extract a best-effort
        # thumbnail using ffmpeg. ``extract_thumbnail`` is non-raising and
        # flag-gated; this step must never fail the job.
        if mode == "video":
            _maybe_extract_thumbnails()
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


def _maybe_extract_thumbnails() -> None:
    """Extract best-effort thumbnails for the MP4 files currently in
    ``VIDEO_DIR``.

    Runs after a successful ``mode == "video"`` download. The yt-dlp output
    template is ``<VIDEO_DIR>/%(title)s.%(ext)s`` and the downloader result
    dict does not currently surface the produced file path, so we scan the
    video directory for ``.mp4`` files and feed each one to
    :func:`extract_thumbnail` (which is non-raising, flag-gated, and skips
    silently when ffmpeg is missing or the input is unreadable).

    This step must never fail the job. Any unexpected error is swallowed and
    logged so a thumbnail/ffmpeg problem cannot turn a completed download
    into a failed one.
    """

    try:
        if not Path(VIDEO_DIR).is_dir():
            return
        for mp4 in sorted(Path(VIDEO_DIR).glob("*.mp4")):
            extract_thumbnail(mp4)
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Thumbnail extraction raised; ignoring")


@router.post("/jobs/{job_id}/complete", response_model=JobResponse, tags=["Jobs"])
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


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Jobs"],
)
def delete_download_job(job_id: str) -> None:
    """Delete a job from the in-memory store (and its SQLite row, if any).

    Returns 204 on success and 404 for unknown job ids. The SQLite ``jobs``
    row is removed best-effort; any database failure is swallowed so the
    in-memory removal still succeeds.
    """

    if not delete_job(job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return None
