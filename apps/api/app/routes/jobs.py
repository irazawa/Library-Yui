from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl

from app.jobs import create_job, get_job, update_job_status

router = APIRouter(tags=["jobs"])


class JobCreateRequest(BaseModel):
    url: HttpUrl


class JobResponse(BaseModel):
    id: str
    url: str
    status: str


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

    This is a stub endpoint: no real download is performed yet. A job that is
    already ``downloading`` or has reached a terminal state (``completed`` /
    ``failed``) is left untouched and returned as-is so callers remain
    idempotent. Unknown job ids return 404.
    """

    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job["status"] == "pending":
        updated = update_job_status(job_id, "downloading")
        if updated is not None:
            return JobResponse(**updated)
    return JobResponse(**job)


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
