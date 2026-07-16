import logging
import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status
from pydantic import BaseModel

from app import database
from app.database import DEFAULT_DB_PATH
from app.storage import AUDIO_DIR, STORAGE_DIRS, UPLOADS_DIR, VIDEO_DIR, ensure_storage_dirs

router = APIRouter(tags=["library"])

logger = logging.getLogger(__name__)

# Maximum accepted upload size (50 MiB). Sized to comfortably accept a typical
# audio file while protecting the server from unbounded payloads.
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

# Database path used by the upload endpoint. Tests override this via
# ``monkeypatch.setattr(library_route, "DB_PATH", tmp_path / "test.db")`` to
# avoid touching the real database file.
DB_PATH: Path | str = DEFAULT_DB_PATH


class LibrarySummaryResponse(BaseModel):
    audio: int
    video: int
    uploads: int
    thumbnails: int


class AudioItem(BaseModel):
    name: str


class AudioListResponse(BaseModel):
    items: list[AudioItem]


class VideoItem(BaseModel):
    name: str


class VideoListResponse(BaseModel):
    items: list[VideoItem]


class UploadResponse(BaseModel):
    id: int
    filename: str
    path: str
    size: int
    content_type: str | None
    uploaded_at: str


class UploadListResponse(BaseModel):
    items: list[UploadResponse]


class TagListResponse(BaseModel):
    items: list[str]


class TagAssignRequest(BaseModel):
    tag: str


class TagAssignResponse(BaseModel):
    metadata_id: int
    tags: list[str]


class MetadataDetailResponse(UploadResponse):
    tags: list[str]


def _count_files(directory: Path) -> int:
    """Count regular files directly inside a storage directory.

    Missing directories count as 0 so the endpoint works before any
    downloads/uploads have happened.
    """

    if not directory.is_dir():
        return 0
    return sum(1 for entry in directory.iterdir() if entry.is_file())


def _payload_too_large() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=f"Upload exceeds the maximum allowed size of {MAX_UPLOAD_BYTES} bytes",
    )


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


@router.get("/library/video", response_model=VideoListResponse)
def list_video() -> VideoListResponse:
    """Return the names of MP4 files in the video library folder.

    Missing directories return an empty list so the endpoint works before
    any downloads have happened.
    """

    if not VIDEO_DIR.is_dir():
        return VideoListResponse(items=[])

    items = [
        VideoItem(name=entry.name)
        for entry in sorted(VIDEO_DIR.iterdir())
        if entry.is_file() and entry.suffix.lower() == ".mp4"
    ]
    return VideoListResponse(items=items)


@router.post(
    "/library/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_file(file: UploadFile) -> UploadResponse:
    """Accept a multipart file upload and save it to ``library/uploads/``.

    The file is streamed to disk in chunks to avoid loading the whole payload
    into memory. After writing, a metadata row is inserted into the SQLite
    database recording the filename, path, size, content type, and timestamp.
    """

    filename = file.filename or "upload.bin"
    content_type = file.content_type

    # Make sure the target directory and database exist before writing.
    ensure_storage_dirs()
    database.init_db(DB_PATH)

    destination = UPLOADS_DIR / filename

    written = 0
    try:
        with destination.open("wb") as out:
            while True:
                chunk = file.file.read(64 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_UPLOAD_BYTES:
                    out.close()
                    destination.unlink(missing_ok=True)
                    raise _payload_too_large()
                out.write(chunk)
    except Exception:
        # Clean up the partial file on any error so we never leave a
        # truncated upload behind.
        destination.unlink(missing_ok=True)
        raise
    finally:
        file.file.close()

    try:
        row_id = database.insert_metadata(
            filename=filename,
            path=str(destination),
            size=written,
            content_type=content_type,
            db_path=DB_PATH,
        )
    except Exception:
        # If the metadata row cannot be recorded, remove the written file so
        # we never leave an orphaned upload on disk that the library does not
        # know about. The caller sees a 500; the filesystem stays consistent.
        destination.unlink(missing_ok=True)
        logger.exception("Failed to record metadata for %s", filename)
        raise

    logger.info("Uploaded %s (%d bytes) as metadata row %d", filename, written, row_id)

    # Build the response from the freshly written row so the returned shape
    # matches exactly what is persisted.
    rows = database.list_metadata(DB_PATH)
    row = next((r for r in rows if r["id"] == row_id), None)
    if row is None:  # pragma: no cover - should be unreachable
        return UploadResponse(
            id=row_id,
            filename=filename,
            path=str(destination),
            size=written,
            content_type=content_type,
            uploaded_at="",
        )
    return UploadResponse(**row)


@router.get("/library/uploads", response_model=UploadListResponse)
def list_uploads(tag: str | None = None, q: str | None = None) -> UploadListResponse:
    """Return uploaded items recorded in the SQLite database.

    Items are returned newest-first. When the database file does not exist
    yet, an empty list is returned so the endpoint works before any uploads
    have happened.

    Optional query params filter the results (combined with AND when both
    are provided):

    - ``tag``: only items that have this tag name attached.
    - ``q``: only items whose ``filename`` contains the substring
      (case-insensitive).
    """

    db_file = Path(DB_PATH)
    if not db_file.is_file():
        return UploadListResponse(items=[])

    try:
        rows = database.list_metadata_filtered(tag=tag, q=q, db_path=DB_PATH)
    except sqlite3.Error:
        # A corrupt/unreadable database should not 500 the whole endpoint;
        # return an empty list and let the logs surface the issue.
        logger.exception("Failed to read uploads from %s", DB_PATH)
        return UploadListResponse(items=[])

    return UploadListResponse(items=[UploadResponse(**row) for row in rows])


@router.get("/library/tags", response_model=TagListResponse)
def list_tags() -> TagListResponse:
    """Return all tag names recorded in the database, alphabetical order.

    Returns ``{"items": []}`` when the database file does not exist yet, so
    the endpoint works before any tags have been created.
    """

    db_file = Path(DB_PATH)
    if not db_file.is_file():
        return TagListResponse(items=[])

    try:
        names = database.list_all_tags(DB_PATH)
    except sqlite3.Error:
        # A corrupt/unreadable database should not 500 the whole endpoint;
        # return an empty list and let the logs surface the issue.
        logger.exception("Failed to read tags from %s", DB_PATH)
        return TagListResponse(items=[])

    return TagListResponse(items=names)


@router.get(
    "/library/metadata/{metadata_id}",
    response_model=MetadataDetailResponse,
)
def get_metadata_detail(metadata_id: int) -> MetadataDetailResponse:
    """Return a single metadata row plus its attached tag list.

    Returns 404 if the database does not exist yet or the row is missing.
    """

    db_file = Path(DB_PATH)
    if not db_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata row not found",
        )

    row = database.get_metadata(metadata_id, DB_PATH)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata row not found",
        )

    tags = database.list_tags_for_metadata(metadata_id, DB_PATH)
    return MetadataDetailResponse(**row, tags=tags)


@router.post(
    "/library/metadata/{metadata_id}/tags",
    response_model=TagAssignResponse,
)
def assign_tag(metadata_id: int, body: TagAssignRequest) -> TagAssignResponse:
    """Attach a tag to a metadata row.

    Returns 404 if the metadata row does not exist. The tag row is created
    automatically and the assignment is idempotent. The response contains the
    metadata id and the full sorted list of tags now attached to that row.
    """

    database.init_db(DB_PATH)
    if not database.metadata_exists(metadata_id, DB_PATH):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata row not found",
        )

    try:
        database.add_tag_to_metadata(metadata_id, body.tag, db_path=DB_PATH)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="tag must be a non-empty string",
        )
    tags = database.list_tags_for_metadata(metadata_id, DB_PATH)
    return TagAssignResponse(metadata_id=metadata_id, tags=tags)


@router.delete(
    "/library/metadata/{metadata_id}/tags/{tag}",
    response_model=TagAssignResponse,
)
def remove_tag(metadata_id: int, tag: str) -> TagAssignResponse:
    """Detach a tag from a metadata row.

    Returns 404 if the metadata row does not exist. The detach is idempotent:
    removing a tag that is not attached is a silent no-op. The tag row itself
    is preserved so it can be reused. The response contains the metadata id
    and the full sorted list of tags now attached to that row.
    """

    database.init_db(DB_PATH)
    if not database.metadata_exists(metadata_id, DB_PATH):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata row not found",
        )

    database.remove_tag_from_metadata(metadata_id, tag, db_path=DB_PATH)
    tags = database.list_tags_for_metadata(metadata_id, DB_PATH)
    return TagAssignResponse(metadata_id=metadata_id, tags=tags)
