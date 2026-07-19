import logging
import sqlite3
import struct
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
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
    size: int
    duration: float | None


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


def _probe_mp4_duration(path: Path) -> float | None:
    """Best-effort parse of an MP4/MOV container's duration in seconds.

    Walks the top-level ISO/IEC 14496-12 boxes looking for the first ``moov``
    box and then the first ``mvhd`` box inside it to read the movie header
    (version 0 or 1). Returns the duration in seconds (``timescale``-based)
    or ``None`` when the container cannot be parsed, is truncated, or the
    header is missing. Never raises; all read/parse errors become ``None``.
    """

    try:
        with path.open("rb") as fh:
            return _read_mp4_duration(fh)
    except (OSError, struct.error, ValueError, EOFError):
        return None


def _read_mp4_duration(fh) -> float | None:
    """Read the movie header duration from an open MP4 file handle."""

    moov = _find_top_level_box(fh, b"moov")
    if moov is None:
        return None

    start, end = moov
    fh.seek(start)
    consumed = 8  # header of moov itself has already been accounted for
    while consumed < (end - start):
        header = fh.read(8)
        if len(header) < 8:
            return None
        size, btype = struct.unpack(">I4s", header)
        consumed += 8
        if size == 1:
            # 64-bit largesize follows the type.
            ext = fh.read(8)
            if len(ext) < 8:
                return None
            size = struct.unpack(">Q", ext)[0]
            consumed += 8
        elif size == 0:
            # Box extends to end of file (legal but rare for mvhd).
            size = end - start - (consumed - 8) + 8

        body_len = size - 8
        if btype == b"mvhd":
            body = fh.read(body_len)
            return _decode_mvhd_duration(body)
        # Skip over the body of any non-mvhd box.
        fh.seek(body_len, 1)
        consumed += body_len
    return None


def _decode_mvhd_duration(body: bytes) -> float | None:
    """Decode a movie header (``mvhd``) box body into seconds."""

    if len(body) < 1:
        return None
    version = body[0]
    if version == 1:
        # version(1) flags(3) creation(8) modification(8) timescale(4) duration(8)
        if len(body) < 4 + 8 + 8 + 4 + 8:
            return None
        timescale = struct.unpack(">I", body[4 + 8 + 8 : 4 + 8 + 8 + 4])[0]
        duration = struct.unpack(">Q", body[4 + 8 + 8 + 4 : 4 + 8 + 8 + 4 + 8])[0]
    else:
        # version 0: version(1) flags(3) creation(4) modification(4) timescale(4) duration(4)
        if len(body) < 4 + 4 + 4 + 4 + 4:
            return None
        timescale = struct.unpack(">I", body[4 + 4 + 4 : 4 + 4 + 4 + 4])[0]
        duration = struct.unpack(">I", body[4 + 4 + 4 + 4 : 4 + 4 + 4 + 4 + 4])[0]
    if timescale <= 0:
        return None
    return duration / timescale


def _find_top_level_box(fh, target: bytes) -> tuple[int, int] | None:
    """Return ``(body_start, body_end)`` byte offsets of the first top-level
    ISO/IEC 14496-12 box whose 4-byte type matches ``target``.

    ``body_start`` excludes the 8-byte box header. Scans the whole file from
    the current position. Returns ``None`` if not found. Seeks back to the
    file start before returning.
    """

    fh.seek(0, 2)
    file_end = fh.tell()
    fh.seek(0)
    pos = 0
    while pos + 8 <= file_end:
        fh.seek(pos)
        header = fh.read(8)
        if len(header) < 8:
            return None
        size, btype = struct.unpack(">I4s", header)
        if size == 1:
            ext = fh.read(8)
            if len(ext) < 8:
                return None
            size = struct.unpack(">Q", ext)[0]
        elif size == 0:
            size = file_end - pos
        if size < 8 or pos + size > file_end:
            return None
        if btype == target:
            return (pos + 8, pos + size)
        pos += size
    return None


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

    Each item includes its file size in bytes and the container-decoded
    duration in seconds when the MP4 header can be parsed best-effort.
    Missing directories return an empty list so the endpoint works before
    any downloads have happened.
    """

    if not VIDEO_DIR.is_dir():
        return VideoListResponse(items=[])

    items: list[VideoItem] = []
    for entry in sorted(VIDEO_DIR.iterdir()):
        if not (entry.is_file() and entry.suffix.lower() == ".mp4"):
            continue
        try:
            size = entry.stat().st_size
        except OSError:
            size = 0
        duration = _probe_mp4_duration(entry)
        items.append(VideoItem(name=entry.name, size=size, duration=duration))
    return VideoListResponse(items=items)


def _resolve_video_file(name: str) -> Path | None:
    """Resolve ``name`` to a real .mp4 file inside ``VIDEO_DIR``.

    Returns the resolved :class:`Path` when the name points to an existing
    ``.mp4`` file directly inside the video library directory, or ``None``
    when the file is missing, not an .mp4, or escapes the directory (path
    traversal). ``None`` lets the caller respond with a uniform 404 without
    leaking whether a file exists.
    """

    if not name or "/" in name or "\\" in name:
        return None
    if Path(name).suffix.lower() != ".mp4":
        return None

    try:
        base = VIDEO_DIR.resolve()
    except OSError:
        return None
    try:
        target = (VIDEO_DIR / name).resolve()
    except OSError:
        return None

    # Ensure the resolved target is a direct child of the video directory.
    if target.parent != base:
        return None
    if not target.is_file():
        return None
    return target


@router.get(
    "/library/video/{name}",
    response_class=FileResponse,
)
def stream_video(name: str):
    """Stream a single ``.mp4`` file from ``library/video``.

    Returns a :class:`FileResponse` with ``video/mp4`` media type so clients
    can play it with HTTP range requests. Returns 404 for missing files,
    non-.mp4 names, or any path that escapes the video directory.
    """

    target = _resolve_video_file(name)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    return FileResponse(target, media_type="video/mp4")


def _resolve_audio_file(name: str) -> Path | None:
    """Resolve ``name`` to a real .mp3 file inside ``AUDIO_DIR``.

    Returns the resolved :class:`Path` when the name points to an existing
    ``.mp3`` file directly inside the audio library directory, or ``None``
    when the file is missing, not an .mp3, or escapes the directory (path
    traversal). ``None`` lets the caller respond with a uniform 404 without
    leaking whether a file exists.
    """

    if not name or "/" in name or "\\" in name:
        return None
    if Path(name).suffix.lower() != ".mp3":
        return None

    try:
        base = AUDIO_DIR.resolve()
    except OSError:
        return None
    try:
        target = (AUDIO_DIR / name).resolve()
    except OSError:
        return None

    # Ensure the resolved target is a direct child of the audio directory.
    if target.parent != base:
        return None
    if not target.is_file():
        return None
    return target


@router.get(
    "/library/audio/{name}",
    response_class=FileResponse,
)
def stream_audio(name: str):
    """Stream a single ``.mp3`` file from ``library/audio``.

    Returns a :class:`FileResponse` with ``audio/mpeg`` media type so clients
    can play it with HTTP range requests. Returns 404 for missing files,
    non-.mp3 names, or any path that escapes the audio directory.
    """

    target = _resolve_audio_file(name)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not found",
        )
    return FileResponse(target, media_type="audio/mpeg")


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
