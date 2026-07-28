from pathlib import Path

from fastapi.testclient import TestClient

import main as main_module
from app.routes import library as library_route
from app.storage import (
    AUDIO_DIR,
    LIBRARY_DIR,
    STORAGE_DIRS,
    THUMBNAILS_DIR,
    UPLOADS_DIR,
    VIDEO_DIR,
    ensure_storage_dirs,
)

client = TestClient(main_module.app)


def test_storage_dirs_are_under_library():
    assert LIBRARY_DIR.name == "library"
    for directory in (AUDIO_DIR, VIDEO_DIR, UPLOADS_DIR, THUMBNAILS_DIR):
        assert directory.parent == LIBRARY_DIR


def test_storage_dirs_mapping_keys_match_names():
    assert set(STORAGE_DIRS.keys()) == {"audio", "video", "uploads", "thumbnails"}
    assert STORAGE_DIRS["audio"] == AUDIO_DIR
    assert STORAGE_DIRS["video"] == VIDEO_DIR
    assert STORAGE_DIRS["uploads"] == UPLOADS_DIR
    assert STORAGE_DIRS["thumbnails"] == THUMBNAILS_DIR


def test_ensure_storage_dirs_is_idempotent(tmp_path, monkeypatch):
    # ensure_storage_dirs operates on the real repo paths; calling it twice
    # should not raise even when the directories already exist.
    ensure_storage_dirs()
    ensure_storage_dirs()

    for directory in STORAGE_DIRS.values():
        assert isinstance(directory, Path)


def test_get_library_storage_returns_bytes_for_all_storage_types():
    response = client.get("/library/storage")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"audio", "video", "uploads", "thumbnails"}
    assert all(isinstance(value, int) and value >= 0 for value in body.values())


def test_get_library_storage_calculates_correct_sizes(tmp_path, monkeypatch):
    fake_audio = tmp_path / "audio"
    fake_video = tmp_path / "video"
    fake_uploads = tmp_path / "uploads"
    fake_thumbnails = tmp_path / "thumbnails"

    fake_audio.mkdir()
    fake_video.mkdir()
    fake_uploads.mkdir()
    fake_thumbnails.mkdir()

    (fake_audio / "song1.mp3").write_bytes(b"A" * 100)
    (fake_audio / "song2.mp3").write_bytes(b"B" * 50)
    (fake_video / "movie.mp4").write_bytes(b"V" * 500)
    (fake_uploads / "doc.pdf").write_bytes(b"U" * 1000)
    (fake_thumbnails / "thumb.jpg").write_bytes(b"T" * 20)

    # Subdirectory to ensure it is ignored in file size calculation
    (fake_audio / "subfolder").mkdir()

    fake_storage_dirs = {
        "audio": fake_audio,
        "video": fake_video,
        "uploads": fake_uploads,
        "thumbnails": fake_thumbnails,
    }
    monkeypatch.setattr(library_route, "STORAGE_DIRS", fake_storage_dirs)

    response = client.get("/library/storage")
    assert response.status_code == 200
    assert response.json() == {
        "audio": 150,
        "video": 500,
        "uploads": 1000,
        "thumbnails": 20,
    }


def test_get_library_storage_missing_dirs(tmp_path, monkeypatch):
    fake_storage_dirs = {
        "audio": tmp_path / "non_existent_audio",
        "video": tmp_path / "non_existent_video",
        "uploads": tmp_path / "non_existent_uploads",
        "thumbnails": tmp_path / "non_existent_thumbnails",
    }
    monkeypatch.setattr(library_route, "STORAGE_DIRS", fake_storage_dirs)

    response = client.get("/library/storage")
    assert response.status_code == 200
    assert response.json() == {
        "audio": 0,
        "video": 0,
        "uploads": 0,
        "thumbnails": 0,
    }

