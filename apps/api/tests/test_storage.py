from pathlib import Path

from app.storage import (
    AUDIO_DIR,
    LIBRARY_DIR,
    STORAGE_DIRS,
    THUMBNAILS_DIR,
    UPLOADS_DIR,
    VIDEO_DIR,
    ensure_storage_dirs,
)


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
