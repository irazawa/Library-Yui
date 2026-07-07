from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["version"])


class VersionResponse(BaseModel):
    app_name: str
    version: str
    milestone: str


@router.get("/version", response_model=VersionResponse)
def get_version() -> VersionResponse:
    return VersionResponse(
        app_name="Library-Yui API",
        version="0.1.0",
        milestone="MVP 1 — Audio Downloads",
    )
