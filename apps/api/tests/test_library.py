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
