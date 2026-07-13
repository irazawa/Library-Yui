"""Integration tests for the POST /library/upload endpoint."""

from pathlib import Path

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
