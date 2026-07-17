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
    """GET /library/audio should return only .mp3 files by name, sorted."""

    fake_audio = tmp_path / "audio"
    fake_audio.mkdir()
    (fake_audio / "a.mp3").write_bytes(b"")
    (fake_audio / "B.mp3").write_bytes(b"")
    (fake_audio / "skip.txt").write_bytes(b"")
    (fake_audio / "ignore.MP4").write_bytes(b"")

    monkeypatch.setattr(library_route, "AUDIO_DIR", fake_audio)

    response = client.get("/library/audio")

    assert response.status_code == 200
    body = response.json()
    assert body == {"items": [{"name": "a.mp3"}, {"name": "B.mp3"}]}


def test_library_audio_returns_empty_when_directory_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(library_route, "AUDIO_DIR", tmp_path / "does-not-exist")

    response = client.get("/library/audio")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_library_video_returns_list_of_mp4_files(monkeypatch, tmp_path):
    """GET /library/video should return only .mp4 files by name, sorted."""

    fake_video = tmp_path / "video"
    fake_video.mkdir()
    (fake_video / "a.mp4").write_bytes(b"")
    (fake_video / "B.mp4").write_bytes(b"")
    (fake_video / "skip.txt").write_bytes(b"")
    (fake_video / "ignore.MP3").write_bytes(b"")

    monkeypatch.setattr(library_route, "VIDEO_DIR", fake_video)

    response = client.get("/library/video")

    assert response.status_code == 200
    body = response.json()
    assert body == {"items": [{"name": "a.mp4"}, {"name": "B.mp4"}]}


def test_library_video_returns_empty_when_directory_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(library_route, "VIDEO_DIR", tmp_path / "does-not-exist")

    response = client.get("/library/video")

    assert response.status_code == 200
    assert response.json() == {"items": []}


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
