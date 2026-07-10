from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl

from app.jobs import create_job, get_job

router = APIRouter(tags=["jobs"])


class JobCreateRequest(BaseModel):
    url: HttpUrl


class JobResponse(BaseModel):
    id: str
    url: str
    status: str


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_download_job(payload: JobCreateRequest) -> JobResponse:
    """Accept a YouTube URL and initialize a pending download job."""

    job = create_job(str(payload.url))
    return JobResponse(**job)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_download_job(job_id: str) -> JobResponse:
    """Return the current status of a specific download job."""

    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse(**job)
