import pytest
from fastapi.testclient import TestClient

import main as main_module
from app.routes import library as library_route

client = TestClient(main_module.app)


def test_library_summary_returns_counts_for_all_storage_types():
    response = client.get("/library/summary")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"audio", "video", "uploads", "thumbnails"}
    assert all(isinstance(value, int) and value >= 0 for value in body.values())


def test_library_audio_returns_list_of_mp3_files(monkeypatch, tmp_path):
    """GET /library/audio should return only .mp3 files by name, sorted, with size/duration."""

    fake_audio = tmp_path / "audio"
    fake_audio.mkdir()
    (fake_audio / "a.mp3").write_bytes(b"\x00\x01\x02\x03")
    (fake_audio / "B.mp3").write_bytes(b"\x00")
    (fake_audio / "skip.txt").write_bytes(b"")
    (fake_audio / "ignore.MP4").write_bytes(b"")

    monkeypatch.setattr(library_route, "AUDIO_DIR", fake_audio)

    response = client.get("/library/audio")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "items": [
            {"name": "a.mp3", "size": 4, "duration": None},
            {"name": "B.mp3", "size": 1, "duration": None},
        ]
    }


def test_library_audio_returns_empty_when_directory_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(library_route, "AUDIO_DIR", tmp_path / "does-not-exist")

    response = client.get("/library/audio")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_library_audio_returns_duration_from_container_header(
    monkeypatch, tmp_path
):
    """GET /library/audio exposes a best-effort duration when the .mp3 file
    is wrapped in an MP4/MOV container (probed via the moov/mvhd header)."""

    fake_audio = tmp_path / "audio"
    fake_audio.mkdir()
    payload = _make_minimal_mp4(duration_seconds=3.0, timescale=1000)
    (fake_audio / "clip.mp3").write_bytes(payload)

    monkeypatch.setattr(library_route, "AUDIO_DIR", fake_audio)

    response = client.get("/library/audio")

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    item = items[0]
    assert item["name"] == "clip.mp3"
    assert item["size"] == len(payload)
    assert item["duration"] == pytest.approx(3.0, rel=1e-6)


def test_library_audio_returns_duration_none_for_non_mp4_container(
    monkeypatch, tmp_path
):
    """A plain .mp3 (no MP4 container) still returns name+size and ``None`` duration."""

    fake_audio = tmp_path / "audio"
    fake_audio.mkdir()
    payload = b"ID3" + b"\x00" * 200  # plausible-ish MP3 head, no moov box
    (fake_audio / "song.mp3").write_bytes(payload)

    monkeypatch.setattr(library_route, "AUDIO_DIR", fake_audio)

    response = client.get("/library/audio")

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    item = items[0]
    assert item["name"] == "song.mp3"
    assert item["size"] == len(payload)
    assert item["duration"] is None


def test_library_video_returns_list_of_mp4_files(monkeypatch, tmp_path):
    """GET /library/video should return only .mp4 files by name, sorted, with size/duration."""

    fake_video = tmp_path / "video"
    fake_video.mkdir()
    (fake_video / "a.mp4").write_bytes(b"\x00\x01\x02\x03")
    (fake_video / "B.mp4").write_bytes(b"\x00")
    (fake_video / "skip.txt").write_bytes(b"")
    (fake_video / "ignore.MP3").write_bytes(b"")

    monkeypatch.setattr(library_route, "VIDEO_DIR", fake_video)

    response = client.get("/library/video")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "items": [
            {"name": "a.mp4", "size": 4, "duration": None},
            {"name": "B.mp4", "size": 1, "duration": None},
        ]
    }


def test_library_video_returns_empty_when_directory_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(library_route, "VIDEO_DIR", tmp_path / "does-not-exist")

    response = client.get("/library/video")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def _make_minimal_mp4(duration_seconds: float, timescale: int = 1000) -> bytes:
    """Build a minimal valid MP4 with a moov/mvhd box for duration parsing tests."""

    # version 0 mvhd body: version(1) flags(3) creation(4) modification(4)
    # timescale(4) duration(4) ... remaining fields filled with zeros.
    duration_units = int(duration_seconds * timescale)
    mvhd_body = (
        b"\x00"  # version
        b"\x00\x00\x00"  # flags
        + (0).to_bytes(4, "big")  # creation_time
        + (0).to_bytes(4, "big")  # modification_time
        + timescale.to_bytes(4, "big")  # timescale
        + duration_units.to_bytes(4, "big")  # duration
        + b"\x00" * 80  # remaining mvhd fields (rate, volume, matrix, etc.)
    )
    mvhd_size = 8 + len(mvhd_body)
    mvhd_box = mvhd_size.to_bytes(4, "big") + b"mvhd" + mvhd_body

    # ftyp box so the file is recognizably an MP4.
    ftyp_body = b"isom" + (0x200).to_bytes(4, "big") + b"isom"
    ftyp_box = (8 + len(ftyp_body)).to_bytes(4, "big") + b"ftyp" + ftyp_body

    moov_body = ftyp_box + mvhd_box
    # NOTE: in a real file, moov would only contain mvhd. We embed ftyp
    # to make sure the parser ignores non-mvhd boxes and still finds mvhd.
    moov_body = mvhd_box
    moov_box = (8 + len(moov_body)).to_bytes(4, "big") + b"moov" + moov_body

    return ftyp_box + moov_box


def test_library_video_returns_duration_from_container_header(
    monkeypatch, tmp_path
):
    """GET /library/video parses the moov/mvhd header to expose duration in seconds."""

    fake_video = tmp_path / "video"
    fake_video.mkdir()
    payload = _make_minimal_mp4(duration_seconds=2.5, timescale=1000)
    (fake_video / "clip.mp4").write_bytes(payload)

    monkeypatch.setattr(library_route, "VIDEO_DIR", fake_video)

    response = client.get("/library/video")

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    item = items[0]
    assert item["name"] == "clip.mp4"
    assert item["size"] == len(payload)
    assert item["duration"] == pytest.approx(2.5, rel=1e-6)


def test_library_video_returns_duration_none_for_non_mp4_container(
    monkeypatch, tmp_path
):
    """A .mp4 file whose body is not an MP4 container still returns name+size and None duration."""

    fake_video = tmp_path / "video"
    fake_video.mkdir()
    payload = b"\x00\x00\x00\x20ftypisom" + b"\x00" * 100  # not a real moov
    (fake_video / "garbage.mp4").write_bytes(payload)

    monkeypatch.setattr(library_route, "VIDEO_DIR", fake_video)

    response = client.get("/library/video")

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    item = items[0]
    assert item["name"] == "garbage.mp4"
    assert item["size"] == len(payload)
    assert item["duration"] is None


def test_library_video_by_name_streams_existing_mp4(monkeypatch, tmp_path):
    """GET /library/video/{name} streams an existing .mp4 file body."""

    fake_video = tmp_path / "video"
    fake_video.mkdir()
    payload = b"\x00\x00\x00\x20ftypisom" + b"\x00" * 100
    (fake_video / "clip.mp4").write_bytes(payload)

    monkeypatch.setattr(library_route, "VIDEO_DIR", fake_video)

    response = client.get("/library/video/clip.mp4")

    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp4"
    assert response.content == payload


def test_library_video_by_name_returns_404_for_missing_file(
    monkeypatch, tmp_path
):
    """GET /library/video/{name} 404s when the file does not exist."""

    fake_video = tmp_path / "video"
    fake_video.mkdir()

    monkeypatch.setattr(library_route, "VIDEO_DIR", fake_video)

    response = client.get("/library/video/missing.mp4")

    assert response.status_code == 404
    assert response.json()["detail"] == "Video not found"


def test_library_video_by_name_returns_404_for_non_mp4(monkeypatch, tmp_path):
    """GET /library/video/{name} 404s when the name is not a .mp4 file."""

    fake_video = tmp_path / "video"
    fake_video.mkdir()
    (fake_video / "notes.txt").write_bytes(b"hi")

    monkeypatch.setattr(library_route, "VIDEO_DIR", fake_video)

    response = client.get("/library/video/notes.txt")

    assert response.status_code == 404
    assert response.json()["detail"] == "Video not found"


def test_library_video_by_name_blocks_path_traversal(monkeypatch, tmp_path):
    """GET /library/video/{name} never serves files outside the video dir.

    Separator-bearing names are rejected with 404 by the router (they don't
    match the single-segment ``{name}`` path param), and any name that would
    resolve outside the directory is rejected with 404 by the handler.
    """

    fake_video = tmp_path / "video"
    fake_video.mkdir()
    # Place a file outside the video dir that a naive join would reach.
    (tmp_path / "secret.mp4").write_bytes(b"sensitive")

    monkeypatch.setattr(library_route, "VIDEO_DIR", fake_video)

    # Every path-escaping or slash-bearing name must be rejected with 404
    # and must never return the secret file's bytes.
    for bad in ("../secret.mp4", "..\\secret.mp4", "/etc/passwd", "sub/clip.mp4"):
        response = client.get(f"/library/video/{bad}")
        assert response.status_code == 404, bad
        assert b"sensitive" not in response.content


def test_library_audio_by_name_streams_existing_mp3(monkeypatch, tmp_path):
    """GET /library/audio/{name} streams an existing .mp3 file body."""

    fake_audio = tmp_path / "audio"
    fake_audio.mkdir()
    payload = b"ID3" + b"\x00" * 200  # plausible-ish MP3 head
    (fake_audio / "track.mp3").write_bytes(payload)

    monkeypatch.setattr(library_route, "AUDIO_DIR", fake_audio)

    response = client.get("/library/audio/track.mp3")

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == payload


def test_library_audio_by_name_returns_404_for_missing_file(
    monkeypatch, tmp_path
):
    """GET /library/audio/{name} 404s when the file does not exist."""

    fake_audio = tmp_path / "audio"
    fake_audio.mkdir()

    monkeypatch.setattr(library_route, "AUDIO_DIR", fake_audio)

    response = client.get("/library/audio/missing.mp3")

    assert response.status_code == 404
    assert response.json()["detail"] == "Audio not found"


def test_library_audio_by_name_returns_404_for_non_mp3(monkeypatch, tmp_path):
    """GET /library/audio/{name} 404s when the name is not a .mp3 file."""

    fake_audio = tmp_path / "audio"
    fake_audio.mkdir()
    (fake_audio / "notes.txt").write_bytes(b"hi")

    monkeypatch.setattr(library_route, "AUDIO_DIR", fake_audio)

    response = client.get("/library/audio/notes.txt")

    assert response.status_code == 404
    assert response.json()["detail"] == "Audio not found"


def test_library_audio_by_name_blocks_path_traversal(monkeypatch, tmp_path):
    """GET /library/audio/{name} never serves files outside the audio dir.

    Separator-bearing names are rejected with 404 by the router (they don't
    match the single-segment ``{name}`` path param), and any name that would
    resolve outside the directory is rejected with 404 by the handler.
    """

    fake_audio = tmp_path / "audio"
    fake_audio.mkdir()
    # Place a file outside the audio dir that a naive join would reach.
    (tmp_path / "secret.mp3").write_bytes(b"sensitive")

    monkeypatch.setattr(library_route, "AUDIO_DIR", fake_audio)

    # Every path-escaping or slash-bearing name must be rejected with 404
    # and must never return the secret file's bytes.
    for bad in ("../secret.mp3", "..\\secret.mp3", "/etc/passwd", "sub/track.mp3"):
        response = client.get(f"/library/audio/{bad}")
        assert response.status_code == 404, bad
        assert b"sensitive" not in response.content


def test_library_thumbnail_by_name_serves_existing_jpg(monkeypatch, tmp_path):
    """GET /library/thumbnails/{name} serves an existing .jpg file body."""

    fake_thumbs = tmp_path / "thumbnails"
    fake_thumbs.mkdir()
    payload = b"\xff\xd8\xff\xe0" + b"\x00" * 50  # plausible JPEG head
    (fake_thumbs / "clip.jpg").write_bytes(payload)

    monkeypatch.setattr(library_route, "THUMBNAILS_DIR", fake_thumbs)

    response = client.get("/library/thumbnails/clip.jpg")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content == payload


def test_library_thumbnail_by_name_returns_404_for_missing_file(
    monkeypatch, tmp_path
):
    """GET /library/thumbnails/{name} 404s when the file does not exist."""

    fake_thumbs = tmp_path / "thumbnails"
    fake_thumbs.mkdir()

    monkeypatch.setattr(library_route, "THUMBNAILS_DIR", fake_thumbs)

    response = client.get("/library/thumbnails/missing.jpg")

    assert response.status_code == 404
    assert response.json()["detail"] == "Thumbnail not found"


def test_library_thumbnail_by_name_returns_404_for_non_jpg(monkeypatch, tmp_path):
    """GET /library/thumbnails/{name} 404s when the name is not a .jpg file."""

    fake_thumbs = tmp_path / "thumbnails"
    fake_thumbs.mkdir()
    (fake_thumbs / "notes.txt").write_bytes(b"hi")

    monkeypatch.setattr(library_route, "THUMBNAILS_DIR", fake_thumbs)

    response = client.get("/library/thumbnails/notes.txt")

    assert response.status_code == 404
    assert response.json()["detail"] == "Thumbnail not found"


def test_library_thumbnail_by_name_blocks_path_traversal(monkeypatch, tmp_path):
    """GET /library/thumbnails/{name} never serves files outside the dir.

    Separator-bearing names are rejected with 404 by the router (they don't
    match the single-segment ``{name}`` path param), and any name that would
    resolve outside the directory is rejected with 404 by the handler.
    """

    fake_thumbs = tmp_path / "thumbnails"
    fake_thumbs.mkdir()
    # Place a file outside the thumbnails dir that a naive join would reach.
    (tmp_path / "secret.jpg").write_bytes(b"sensitive")

    monkeypatch.setattr(library_route, "THUMBNAILS_DIR", fake_thumbs)

    # Every path-escaping or slash-bearing name must be rejected with 404
    # and must never return the secret file's bytes.
    for bad in ("../secret.jpg", "..\\secret.jpg", "/etc/passwd", "sub/clip.jpg"):
        response = client.get(f"/library/thumbnails/{bad}")
        assert response.status_code == 404, bad
        assert b"sensitive" not in response.content


def test_library_tags_returns_empty_when_no_db(monkeypatch, tmp_path):
    """GET /library/tags returns {"items": []} before any database exists."""

    monkeypatch.setattr(library_route, "DB_PATH", tmp_path / "missing.db")

    response = client.get("/library/tags")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_library_tags_returns_all_tags_alphabetical(monkeypatch, tmp_path):
    """GET /library/tags returns every tag name, sorted alphabetically."""

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(library_route, "DB_PATH", db_path)

    # Seed the database with metadata + tags via the database helpers.
    from app import database

    database.init_db(db_path)
    metadata_id = database.insert_metadata(
        filename="song.mp3",
        path=str(tmp_path / "song.mp3"),
        size=123,
        content_type="audio/mpeg",
        db_path=db_path,
    )
    database.add_tag_to_metadata(metadata_id, "chill", db_path=db_path)
    database.add_tag_to_metadata(metadata_id, "Ambient", db_path=db_path)
    # Attach a second metadata row to a tag that already exists (idempotent).
    other_id = database.insert_metadata(
        filename="track.mp3",
        path=str(tmp_path / "track.mp3"),
        size=456,
        content_type="audio/mpeg",
        db_path=db_path,
    )
    database.add_tag_to_metadata(other_id, "chill", db_path=db_path)

    response = client.get("/library/tags")

    assert response.status_code == 200
    # SQLite ORDER BY name is case-sensitive (ASCII uppercase first).
    assert response.json() == {"items": ["Ambient", "chill"]}


def test_assign_tag_attaches_and_returns_sorted_list(monkeypatch, tmp_path):
    """POST /library/metadata/{id}/tags attaches a tag and returns all tags."""

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(library_route, "DB_PATH", db_path)

    from app import database

    database.init_db(db_path)
    metadata_id = database.insert_metadata(
        filename="song.mp3",
        path=str(tmp_path / "song.mp3"),
        size=10,
        content_type="audio/mpeg",
        db_path=db_path,
    )

    response = client.post(
        f"/library/metadata/{metadata_id}/tags", json={"tag": "chill"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["metadata_id"] == metadata_id
    assert body["tags"] == ["chill"]

    # Adding a second tag returns both sorted.
    response = client.post(
        f"/library/metadata/{metadata_id}/tags", json={"tag": "Ambient"}
    )
    assert response.status_code == 200
    assert response.json()["tags"] == ["Ambient", "chill"]


def test_assign_tag_is_idempotent(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(library_route, "DB_PATH", db_path)

    from app import database

    database.init_db(db_path)
    metadata_id = database.insert_metadata(
        filename="song.mp3",
        path=str(tmp_path / "song.mp3"),
        size=10,
        content_type="audio/mpeg",
        db_path=db_path,
    )

    for _ in range(2):
        response = client.post(
            f"/library/metadata/{metadata_id}/tags", json={"tag": "chill"}
        )
        assert response.status_code == 200
    assert response.json()["tags"] == ["chill"]


def test_assign_tag_unknown_metadata_returns_404(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(library_route, "DB_PATH", db_path)

    from app import database

    database.init_db(db_path)

    response = client.post("/library/metadata/9999/tags", json={"tag": "chill"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Metadata row not found"


def test_assign_tag_rejects_empty_tag(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(library_route, "DB_PATH", db_path)

    from app import database

    database.init_db(db_path)
    metadata_id = database.insert_metadata(
        filename="song.mp3",
        path=str(tmp_path / "song.mp3"),
        size=10,
        content_type="audio/mpeg",
        db_path=db_path,
    )

    response = client.post(
        f"/library/metadata/{metadata_id}/tags", json={"tag": "   "}
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "tag must be a non-empty string"


def test_remove_tag_detaches_and_returns_remaining(monkeypatch, tmp_path):
    """DELETE /library/metadata/{id}/tags/{tag} detaches and returns list."""

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(library_route, "DB_PATH", db_path)

    from app import database

    database.init_db(db_path)
    metadata_id = database.insert_metadata(
        filename="song.mp3",
        path=str(tmp_path / "song.mp3"),
        size=10,
        content_type="audio/mpeg",
        db_path=db_path,
    )
    database.add_tag_to_metadata(metadata_id, "chill", db_path=db_path)
    database.add_tag_to_metadata(metadata_id, "Ambient", db_path=db_path)

    response = client.delete(f"/library/metadata/{metadata_id}/tags/chill")

    assert response.status_code == 200
    body = response.json()
    assert body["metadata_id"] == metadata_id
    assert body["tags"] == ["Ambient"]


def test_remove_tag_is_idempotent_when_not_attached(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(library_route, "DB_PATH", db_path)

    from app import database

    database.init_db(db_path)
    metadata_id = database.insert_metadata(
        filename="song.mp3",
        path=str(tmp_path / "song.mp3"),
        size=10,
        content_type="audio/mpeg",
        db_path=db_path,
    )

    # Removing a tag that was never attached is a no-op.
    response = client.delete(f"/library/metadata/{metadata_id}/tags/never")

    assert response.status_code == 200
    assert response.json()["tags"] == []


def test_remove_tag_unknown_metadata_returns_404(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(library_route, "DB_PATH", db_path)

    from app import database

    database.init_db(db_path)

    response = client.delete("/library/metadata/9999/tags/chill")

    assert response.status_code == 404
    assert response.json()["detail"] == "Metadata row not found"


def test_get_metadata_detail_returns_row_with_tags(monkeypatch, tmp_path):
    """GET /library/metadata/{id} returns the row fields plus sorted tags."""

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(library_route, "DB_PATH", db_path)

    from app import database

    database.init_db(db_path)
    metadata_id = database.insert_metadata(
        filename="song.mp3",
        path=str(tmp_path / "song.mp3"),
        size=123,
        content_type="audio/mpeg",
        db_path=db_path,
    )
    database.add_tag_to_metadata(metadata_id, "chill", db_path=db_path)
    database.add_tag_to_metadata(metadata_id, "Ambient", db_path=db_path)

    response = client.get(f"/library/metadata/{metadata_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == metadata_id
    assert body["filename"] == "song.mp3"
    assert body["size"] == 123
    assert body["content_type"] == "audio/mpeg"
    assert body["uploaded_at"]
    # SQLite ORDER BY name is case-sensitive (ASCII uppercase first).
    assert body["tags"] == ["Ambient", "chill"]


def test_get_metadata_detail_without_tags_returns_empty_list(
    monkeypatch, tmp_path
):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(library_route, "DB_PATH", db_path)

    from app import database

    database.init_db(db_path)
    metadata_id = database.insert_metadata(
        filename="plain.bin",
        path=str(tmp_path / "plain.bin"),
        size=1,
        content_type=None,
        db_path=db_path,
    )

    response = client.get(f"/library/metadata/{metadata_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == metadata_id
    assert body["tags"] == []


def test_get_metadata_detail_unknown_id_returns_404(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(library_route, "DB_PATH", db_path)

    from app import database

    database.init_db(db_path)

    response = client.get("/library/metadata/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Metadata row not found"


def test_get_metadata_detail_missing_db_returns_404(monkeypatch, tmp_path):
    monkeypatch.setattr(library_route, "DB_PATH", tmp_path / "missing.db")

    response = client.get("/library/metadata/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Metadata row not found"
