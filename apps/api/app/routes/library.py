from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from app.storage import STORAGE_DIRS

router = APIRouter(tags=["library"])


class LibrarySummaryResponse(BaseModel):
    audio: int
    video: int
    uploads: int
    thumbnails: int


def _count_files(directory: Path) -> int:
    """Count regular files directly inside a storage directory.

    Missing directories count as 0 so the endpoint works before any
    downloads/uploads have happened.
    """

    if not directory.is_dir():
        return 0
    return sum(1 for entry in directory.iterdir() if entry.is_file())


@router.get("/library/summary", response_model=LibrarySummaryResponse)
def get_library_summary() -> LibrarySummaryResponse:
    counts = {name: _count_files(path) for name, path in STORAGE_DIRS.items()}
    return LibrarySummaryResponse(**counts)
