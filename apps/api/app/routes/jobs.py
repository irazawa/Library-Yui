from fastapi import APIRouter, status
from pydantic import BaseModel, HttpUrl

from app.jobs import create_job

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
