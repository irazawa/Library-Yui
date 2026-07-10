from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from app.storage import AUDIO_DIR, STORAGE_DIRS

router = APIRouter(tags=["library"])


class LibrarySummaryResponse(BaseModel):
    audio: int
    video: int
    uploads: int
    thumbnails: int


class AudioItem(BaseModel):
    name: str


class AudioListResponse(BaseModel):
    items: list[AudioItem]


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


@router.get("/library/audio", response_model=AudioListResponse)
def list_audio() -> AudioListResponse:
    """Return the names of MP3 files in the audio library folder.

    Missing directories return an empty list so the endpoint works before
    any downloads have happened.
    """

    if not AUDIO_DIR.is_dir():
        return AudioListResponse(items=[])

    items = [
        AudioItem(name=entry.name)
        for entry in sorted(AUDIO_DIR.iterdir())
        if entry.is_file() and entry.suffix.lower() == ".mp3"
    ]
    return AudioListResponse(items=items)
