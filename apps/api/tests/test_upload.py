"""Integration tests for the POST /library/upload endpoint."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main as main_module
from app.routes import library as library_route

client = TestClient(main_module.app)


def _setup_isolated_storage(monkeypatch, tmp_path):
    """Point the upload route at an isolated uploads dir + database.

    Returns the (uploads_dir, db_path) tuple so each test can assert on them.
    """

    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    db_path = tmp_path / "library.db"

    monkeypatch.setattr(library_route, "UPLOADS_DIR", uploads_dir)
    monkeypatch.setattr(library_route, "DB_PATH", db_path)
    return uploads_dir, db_path


def test_upload_writes_file_to_uploads_and_returns_201(monkeypatch, tmp_path):
    uploads_dir, db_path = _setup_isolated_storage(monkeypatch, tmp_path)

    payload = b"fake-audio-bytes"
    response = client.post(
        "/library/upload",
        files={"file": ("song.mp3", payload, "audio/mpeg")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "song.mp3"
    assert body["size"] == len(payload)
    assert body["content_type"] == "audio/mpeg"
    assert body["id"] > 0
    assert body["uploaded_at"]
    assert "T" in body["uploaded_at"]

    # File should exist on disk.
    written_file = uploads_dir / "song.mp3"
    assert written_file.is_file()
    assert written_file.read_bytes() == payload


def test_upload_records_metadata_in_database(monkeypatch, tmp_path):
    uploads_dir, db_path = _setup_isolated_storage(monkeypatch, tmp_path)

    payload = b"hello world"
    response = client.post(
        "/library/upload",
        files={"file": ("note.txt", payload, "text/plain")},
    )

    assert response.status_code == 201
    from app import database

    rows = database.list_metadata(db_path)
    assert len(rows) == 1
    row = rows[0]
    assert row["filename"] == "note.txt"
    assert row["size"] == len(payload)
    assert row["content_type"] == "text/plain"
    assert row["path"].endswith("note.txt")


def test_upload_missing_file_field_returns_422(monkeypatch, tmp_path):
    _setup_isolated_storage(monkeypatch, tmp_path)

    response = client.post("/library/upload", files={})

    assert response.status_code == 422


def test_upload_preserves_filename_with_dots(monkeypatch, tmp_path):
    uploads_dir, _ = _setup_isolated_storage(monkeypatch, tmp_path)

    response = client.post(
        "/library/upload",
        files={"file": ("my.track.v2.mp3", b"data", "audio/mpeg")},
    )

    assert response.status_code == 201
    assert (uploads_dir / "my.track.v2.mp3").is_file()


def test_upload_empty_file_is_allowed(monkeypatch, tmp_path):
    uploads_dir, _ = _setup_isolated_storage(monkeypatch, tmp_path)

    response = client.post(
        "/library/upload",
        files={"file": ("empty.mp3", b"", "audio/mpeg")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["size"] == 0
    assert (uploads_dir / "empty.mp3").is_file()


def test_upload_multiple_files_each_get_unique_row(monkeypatch, tmp_path):
    uploads_dir, db_path = _setup_isolated_storage(monkeypatch, tmp_path)

    r1 = client.post(
        "/library/upload",
        files={"file": ("a.mp3", b"aaaa", "audio/mpeg")},
    )
    r2 = client.post(
        "/library/upload",
        files={"file": ("b.mp3", b"bbbb", "audio/mpeg")},
    )

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] != r2.json()["id"]

    from app import database

    rows = database.list_metadata(db_path)
    assert len(rows) == 2
    filenames = {r["filename"] for r in rows}
    assert filenames == {"a.mp3", "b.mp3"}


def test_upload_persists_uploaded_at_timestamp(monkeypatch, tmp_path):
    uploads_dir, db_path = _setup_isolated_storage(monkeypatch, tmp_path)

    response = client.post(
        "/library/upload",
        files={"file": ("ts.mp3", b"data", "audio/mpeg")},
    )

    assert response.status_code == 201
    from datetime import datetime

    from app import database

    rows = database.list_metadata(db_path)
    assert len(rows) == 1
    # uploaded_at must be a parseable ISO-8601 timestamp, not empty.
    parsed = datetime.fromisoformat(rows[0]["uploaded_at"])
    assert parsed.tzinfo is not None, "uploaded_at must be timezone-aware"


def test_upload_removes_file_when_metadata_insert_fails(monkeypatch, tmp_path):
    uploads_dir, db_path = _setup_isolated_storage(monkeypatch, tmp_path)

    # Force the metadata insert to raise so we can verify the orphan-cleanup
    # path: the uploaded file must be removed, not left behind on disk.
    from app import database

    def _boom(**kwargs):
        raise RuntimeError("simulated db failure")

    monkeypatch.setattr(database, "insert_metadata", _boom)
    monkeypatch.setattr(library_route.database, "insert_metadata", _boom)

    # TestClient re-raises server exceptions by default; the important
    # contract under test is the filesystem side-effect (orphan cleanup),
    # not the HTTP status code.
    with pytest.raises(RuntimeError, match="simulated db failure"):
        client.post(
            "/library/upload",
            files={"file": ("orphan.mp3", b"data", "audio/mpeg")},
        )

    # No orphan file must remain on disk.
    assert not (uploads_dir / "orphan.mp3").exists()
    # And no row must be recorded.
    assert database.list_metadata(db_path) == []


def test_upload_rejects_file_exceeding_size_cap(monkeypatch, tmp_path):
    """A payload over MAX_UPLOAD_BYTES is rejected with 413 and leaves no
    partial file on disk and no metadata row in the database."""

    uploads_dir, db_path = _setup_isolated_storage(monkeypatch, tmp_path)

    # Payload slightly larger than the 50 MiB cap defined on the route.
    from app.routes.library import MAX_UPLOAD_BYTES

    overflow_size = MAX_UPLOAD_BYTES + 1024
    payload = b"\0" * overflow_size

    response = client.post(
        "/library/upload",
        files={"file": ("too_big.mp3", payload, "audio/mpeg")},
    )

    assert response.status_code == 413

    # No partial upload may be left on disk.
    assert not (uploads_dir / "too_big.mp3").exists()

    # And no metadata row may have been recorded.
    from app import database

    assert database.list_metadata(db_path) == []


def test_upload_writes_multichunk_file(monkeypatch, tmp_path):
    """A payload larger than a single 64 KiB chunk is streamed across multiple
    writes and reconstructed byte-for-byte on disk."""

    uploads_dir, db_path = _setup_isolated_storage(monkeypatch, tmp_path)

    # Three chunks worth of distinct bytes (> 64 KiB guarantees the route's
    # chunked-read loop executes more than once).
    payload = (b"AB" * 40 * 1024) + (b"CD" * 40 * 1024) + b"tail"
    assert len(payload) > 64 * 1024

    response = client.post(
        "/library/upload",
        files={"file": ("multi.mp3", payload, "audio/mpeg")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["size"] == len(payload)

    written = (uploads_dir / "multi.mp3").read_bytes()
    assert written == payload


def test_list_uploads_empty_when_no_database(monkeypatch, tmp_path):
    """GET /library/uploads returns {"items": []} when no db file exists yet."""

    _setup_isolated_storage(monkeypatch, tmp_path)

    response = client.get("/library/uploads")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_list_uploads_returns_recorded_uploads_newest_first(monkeypatch, tmp_path):
    """GET /library/uploads returns all uploaded items, newest first."""

    _setup_isolated_storage(monkeypatch, tmp_path)

    # Upload two distinct files.
    r1 = client.post(
        "/library/upload",
        files={"file": ("first.mp3", b"aaaa", "audio/mpeg")},
    )
    r2 = client.post(
        "/library/upload",
        files={"file": ("second.mp3", b"bbbb", "audio/mpeg")},
    )
    assert r1.status_code == 201
    assert r2.status_code == 201

    response = client.get("/library/uploads")

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 2

    # Newest first: second.mp3 then first.mp3.
    assert items[0]["filename"] == "second.mp3"
    assert items[1]["filename"] == "first.mp3"
    # Each item exposes the full metadata contract.
    for item in items:
        assert set(item.keys()) == {
            "id",
            "filename",
            "path",
            "size",
            "content_type",
            "uploaded_at",
        }
        assert item["content_type"] == "audio/mpeg"
        assert item["uploaded_at"]


def test_list_uploads_reflects_new_upload(monkeypatch, tmp_path):
    """A subsequent GET /library/uploads reflects a newly uploaded file."""

    _setup_isolated_storage(monkeypatch, tmp_path)

    assert client.get("/library/uploads").json()["items"] == []

    client.post(
        "/library/upload",
        files={"file": ("late.mp3", b"cc", "audio/mpeg")},
    )

    items = client.get("/library/uploads").json()["items"]
    assert len(items) == 1
    assert items[0]["filename"] == "late.mp3"
