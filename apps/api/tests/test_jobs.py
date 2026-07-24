from fastapi.testclient import TestClient

from app import database
from app import downloader as downloader_mod
from app import jobs as jobs_mod
from app.downloader import DOWNLOADS_ENABLED_FLAG
from app.jobs import create_job, get_job, reset_jobs, set_jobs_db_path
from app.routes import jobs as jobs_routes
from main import app


def setup_function() -> None:
    reset_jobs()


def test_create_job_returns_201_with_id_and_pending_status():
    client = TestClient(app)

    response = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    )

    assert response.status_code == 201
    body = response.json()
    assert "id" in body and isinstance(body["id"], str) and len(body["id"]) > 0
    assert body["url"].startswith("https://")
    assert body["status"] == "pending"


def test_create_job_stores_job_state():
    client = TestClient(app)

    response = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    )
    job_id = response.json()["id"]

    # A second request with the same URL should create a different job.
    second = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    )
    assert second.json()["id"] != job_id


def test_get_job_returns_status():
    client = TestClient(app)

    created = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    ).json()

    response = client.get(f"/jobs/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["url"] == created["url"]
    assert body["status"] == "pending"


def test_get_job_unknown_id_returns_404() -> None:
    client = TestClient(app)

    response = client.get("/jobs/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_create_job_rejects_non_youtube_url() -> None:
    client = TestClient(app)

    response = client.post(
        "/jobs",
        json={"url": "https://example.com/watch?v=abc"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Only YouTube URLs are accepted"


def test_create_job_accepts_youtu_be_short_url() -> None:
    client = TestClient(app)

    response = client.post(
        "/jobs",
        json={"url": "https://youtu.be/dQw4w9WgXcQ"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_create_job_accepts_music_youtube_url() -> None:
    client = TestClient(app)

    response = client.post(
        "/jobs",
        json={"url": "https://music.youtube.com/watch?v=abc123"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_start_job_transitions_pending_to_downloading() -> None:
    client = TestClient(app)

    created = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    ).json()
    job_id = created["id"]

    response = client.post(f"/jobs/{job_id}/start")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == job_id
    assert body["status"] == "downloading"


def test_start_job_is_idempotent_when_already_downloading() -> None:
    client = TestClient(app)

    created = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    ).json()
    job_id = created["id"]

    client.post(f"/jobs/{job_id}/start")
    second = client.post(f"/jobs/{job_id}/start")

    assert second.status_code == 200
    assert second.json()["status"] == "downloading"


def test_start_job_unknown_id_returns_404() -> None:
    client = TestClient(app)

    response = client.post("/jobs/does-not-exist/start")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_complete_job_transitions_downloading_to_completed() -> None:
    client = TestClient(app)

    created = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    ).json()
    job_id = created["id"]
    client.post(f"/jobs/{job_id}/start")

    response = client.post(f"/jobs/{job_id}/complete")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == job_id
    assert body["status"] == "completed"


def test_complete_job_is_idempotent_when_already_completed() -> None:
    client = TestClient(app)

    created = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    ).json()
    job_id = created["id"]
    client.post(f"/jobs/{job_id}/start")
    client.post(f"/jobs/{job_id}/complete")

    second = client.post(f"/jobs/{job_id}/complete")

    assert second.status_code == 200
    assert second.json()["status"] == "completed"


def test_complete_job_unknown_id_returns_404() -> None:
    client = TestClient(app)

    response = client.post("/jobs/does-not-exist/complete")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_list_jobs_returns_empty_when_none() -> None:
    client = TestClient(app)

    response = client.get("/jobs")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_list_jobs_returns_all_created_jobs() -> None:
    client = TestClient(app)

    first = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    ).json()
    second = client.post(
        "/jobs",
        json={"url": "https://youtu.be/abcdefghijk"},
    ).json()

    response = client.get("/jobs")

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 2
    # Insertion order is preserved.
    assert items[0]["id"] == first["id"]
    assert items[1]["id"] == second["id"]
    for item in items:
        assert {"id", "url", "status", "mode"} == set(item.keys())
        assert item["status"] == "pending"
        assert item["mode"] == "audio"


def test_job_lifecycle_pending_to_downloading_to_completed() -> None:
    """Cover the full happy-path lifecycle of a single job in one sequence.

    The job is created as ``pending``, transitioned to ``downloading`` via
    ``POST /jobs/{id}/start``, and finally transitioned to ``completed`` via
    ``POST /jobs/{id}/complete``. Each step asserts both the response status
    code and the returned job status so the lifecycle contract is documented
    in one place.
    """

    client = TestClient(app)

    # Step 1 — create a pending job.
    created = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    ).json()
    job_id = created["id"]
    assert created["status"] == "pending"

    # A freshly created job should still read as pending before any transition.
    fresh = client.get(f"/jobs/{job_id}").json()
    assert fresh["status"] == "pending"

    # Step 2 — pending → downloading.
    started = client.post(f"/jobs/{job_id}/start")
    assert started.status_code == 200
    assert started.json()["status"] == "downloading"

    # GET should reflect the new status.
    after_start = client.get(f"/jobs/{job_id}").json()
    assert after_start["status"] == "downloading"

    # Step 3 — downloading → completed.
    completed = client.post(f"/jobs/{job_id}/complete")
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    # The final GET should show the terminal status.
    after_complete = client.get(f"/jobs/{job_id}").json()
    assert after_complete["status"] == "completed"
    assert after_complete["id"] == job_id
    assert after_complete["url"] == created["url"]


# ---------------------------------------------------------------------------
# Real-download wiring (flag-gated) tests for POST /jobs/{id}/start
# ---------------------------------------------------------------------------

def test_start_job_runs_download_and_completes_when_flag_enabled(monkeypatch):
    """When the download flag is on and download_mp3 succeeds, ``/start``
    should run the real download and end the job in ``completed``."""

    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")

    captured = {}

    def fake_download(url, output_dir=None):
        captured["url"] = url
        return {"ok": True, "returncode": 0, "command": ["yt-dlp", url]}

    monkeypatch.setattr(jobs_routes, "download_mp3", fake_download)

    client = TestClient(app)
    created = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    ).json()
    job_id = created["id"]

    response = client.post(f"/jobs/{job_id}/start")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert captured["url"] == created["url"]


def test_start_job_marks_failed_when_download_returns_error(monkeypatch):
    """When the download flag is on but download_mp3 reports failure (non-zero
    exit), the job should end in ``failed``."""

    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")

    def fake_download(url, output_dir=None):
        return {"ok": False, "returncode": 1, "command": ["yt-dlp", url]}

    monkeypatch.setattr(jobs_routes, "download_mp3", fake_download)

    client = TestClient(app)
    created = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    ).json()
    job_id = created["id"]

    response = client.post(f"/jobs/{job_id}/start")

    assert response.status_code == 200
    assert response.json()["status"] == "failed"


def test_start_job_skips_download_when_flag_disabled(monkeypatch):
    """When the flag is off, ``/start`` must NOT call download_mp3 and the job
    stays in ``downloading`` (stub behavior)."""

    monkeypatch.delenv(DOWNLOADS_ENABLED_FLAG, raising=False)

    called = {"count": 0}

    def fake_download(url, output_dir=None):
        called["count"] += 1
        return {"ok": True, "returncode": 0, "command": []}

    monkeypatch.setattr(jobs_routes, "download_mp3", fake_download)

    client = TestClient(app)
    created = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    ).json()
    job_id = created["id"]

    response = client.post(f"/jobs/{job_id}/start")

    assert response.status_code == 200
    assert response.json()["status"] == "downloading"
    assert called["count"] == 0


def test_start_job_marks_failed_when_download_raises(monkeypatch):
    """When download_mp3 raises, the job should be marked ``failed`` and the
    exception re-raised is avoided (the route catches it)."""

    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")

    def fake_download(url, output_dir=None):
        raise RuntimeError("yt-dlp not found")

    monkeypatch.setattr(jobs_routes, "download_mp3", fake_download)

    client = TestClient(app)
    created = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    ).json()
    job_id = created["id"]

    response = client.post(f"/jobs/{job_id}/start")

    assert response.status_code == 200
    assert response.json()["status"] == "failed"


def test_start_job_calls_download_mp4_for_video_mode(monkeypatch):
    """When ``mode == "video"`` and the flag is on, ``/start`` must dispatch
    to :func:`download_mp4` (not ``download_mp3``) and complete the job."""

    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")

    calls = {"mp3": 0, "mp4": 0}

    def fake_mp3(url, output_dir=None):
        calls["mp3"] += 1
        return {"ok": True, "returncode": 0, "command": ["yt-dlp", url]}

    def fake_mp4(url, output_dir=None):
        calls["mp4"] += 1
        return {"ok": True, "returncode": 0, "command": ["yt-dlp", url]}

    monkeypatch.setattr(jobs_routes, "download_mp3", fake_mp3)
    monkeypatch.setattr(jobs_routes, "download_mp4", fake_mp4)

    client = TestClient(app)
    created = client.post(
        "/jobs",
        json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "mode": "video",
        },
    ).json()
    job_id = created["id"]

    response = client.post(f"/jobs/{job_id}/start")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert calls["mp4"] == 1
    assert calls["mp3"] == 0


def test_start_job_calls_download_mp3_for_audio_mode(monkeypatch):
    """When ``mode == "audio"`` (default) and the flag is on, ``/start`` must
    dispatch to :func:`download_mp3` (not ``download_mp4``)."""

    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")

    calls = {"mp3": 0, "mp4": 0}

    def fake_mp3(url, output_dir=None):
        calls["mp3"] += 1
        return {"ok": True, "returncode": 0, "command": ["yt-dlp", url]}

    def fake_mp4(url, output_dir=None):
        calls["mp4"] += 1
        return {"ok": True, "returncode": 0, "command": ["yt-dlp", url]}

    monkeypatch.setattr(jobs_routes, "download_mp3", fake_mp3)
    monkeypatch.setattr(jobs_routes, "download_mp4", fake_mp4)

    client = TestClient(app)
    created = client.post(
        "/jobs",
        json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "mode": "audio",
        },
    ).json()
    job_id = created["id"]

    response = client.post(f"/jobs/{job_id}/start")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert calls["mp3"] == 1
    assert calls["mp4"] == 0


# ---------------------------------------------------------------------------
# Thumbnail extraction wiring (mode == "video", flag-gated, best-effort)
# ---------------------------------------------------------------------------

def test_start_job_video_mode_invokes_thumbnail_extraction(monkeypatch):
    """A successful ``mode == "video"`` download should trigger the
    best-effort thumbnail extraction step (``extract_thumbnail``), while the
    job still ends in ``completed``."""

    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")

    def fake_mp4(url, output_dir=None):
        return {"ok": True, "returncode": 0, "command": ["yt-dlp", url]}

    # Capture thumbnail extraction calls. We monkeypatch the function on the
    # routes module because that is the name imported there.
    thumb_calls = {"count": 0}

    def fake_extract(*args, **kwargs):
        thumb_calls["count"] += 1
        return {"ok": True, "skipped": False, "path": "fake", "returncode": 0}

    monkeypatch.setattr(jobs_routes, "download_mp4", fake_mp4)
    monkeypatch.setattr(jobs_routes, "extract_thumbnail", fake_extract)
    # Give VIDEO_DIR a real tmp dir with one fake mp4 so the helper reaches
    # the extract_thumbnail call.
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as d:
        video_dir = Path(d)
        (video_dir / "clip.mp4").write_bytes(b"fake")
        monkeypatch.setattr(jobs_routes, "VIDEO_DIR", video_dir)

        client = TestClient(app)
        created = client.post(
            "/jobs",
            json={
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "mode": "video",
            },
        ).json()
        job_id = created["id"]

        response = client.post(f"/jobs/{job_id}/start")

        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert thumb_calls["count"] == 1


def test_start_job_audio_mode_does_not_invoke_thumbnail_extraction(monkeypatch):
    """A ``mode == "audio"`` download must NOT trigger thumbnail extraction."""

    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")

    def fake_mp3(url, output_dir=None):
        return {"ok": True, "returncode": 0, "command": ["yt-dlp", url]}

    thumb_calls = {"count": 0}

    def fake_extract(*args, **kwargs):
        thumb_calls["count"] += 1
        return {"ok": False, "skipped": True, "path": None, "returncode": None}

    monkeypatch.setattr(jobs_routes, "download_mp3", fake_mp3)
    monkeypatch.setattr(jobs_routes, "extract_thumbnail", fake_extract)

    client = TestClient(app)
    created = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    ).json()
    job_id = created["id"]

    response = client.post(f"/jobs/{job_id}/start")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert thumb_calls["count"] == 0


def test_start_job_video_mode_thumbnail_failure_does_not_fail_job(monkeypatch):
    """If ``extract_thumbnail`` raises, the job must still report
    ``completed`` — the thumbnail step is best-effort and never fails the
    job."""

    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")

    def fake_mp4(url, output_dir=None):
        return {"ok": True, "returncode": 0, "command": ["yt-dlp", url]}

    def exploding_extract(*args, **kwargs):
        raise RuntimeError("ffmpeg exploded")

    monkeypatch.setattr(jobs_routes, "download_mp4", fake_mp4)
    monkeypatch.setattr(jobs_routes, "extract_thumbnail", exploding_extract)

    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as d:
        video_dir = Path(d)
        (video_dir / "clip.mp4").write_bytes(b"fake")
        monkeypatch.setattr(jobs_routes, "VIDEO_DIR", video_dir)

        client = TestClient(app)
        created = client.post(
            "/jobs",
            json={
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "mode": "video",
            },
        ).json()
        job_id = created["id"]

        response = client.post(f"/jobs/{job_id}/start")

        assert response.status_code == 200
        assert response.json()["status"] == "completed"


def test_start_job_video_mode_skips_thumbnail_when_video_dir_missing(monkeypatch):
    """When ``VIDEO_DIR`` does not exist on disk, thumbnail extraction is
    skipped silently — the helper must not crash and the job still completes."""

    monkeypatch.setenv(DOWNLOADS_ENABLED_FLAG, "1")

    def fake_mp4(url, output_dir=None):
        return {"ok": True, "returncode": 0, "command": ["yt-dlp", url]}

    thumb_calls = {"count": 0}

    def fake_extract(*args, **kwargs):
        thumb_calls["count"] += 1
        return {"ok": False, "skipped": True, "path": None, "returncode": None}

    monkeypatch.setattr(jobs_routes, "download_mp4", fake_mp4)
    monkeypatch.setattr(jobs_routes, "extract_thumbnail", fake_extract)
    # Point VIDEO_DIR at a path that does not exist.
    monkeypatch.setattr(jobs_routes, "VIDEO_DIR", __import__("pathlib").Path("/no/such/dir/xyz"))

    client = TestClient(app)
    created = client.post(
        "/jobs",
        json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "mode": "video",
        },
    ).json()
    job_id = created["id"]

    response = client.post(f"/jobs/{job_id}/start")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert thumb_calls["count"] == 0


# ---------------------------------------------------------------------------
# POST /jobs `mode` field (audio | video)
# ---------------------------------------------------------------------------

def test_create_job_defaults_mode_to_audio_when_omitted() -> None:
    """When ``mode`` is omitted the job is created in ``audio`` mode."""

    client = TestClient(app)
    created = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    ).json()

    assert created["mode"] == "audio"

    # The persisted job should also carry the default mode.
    fetched = client.get(f"/jobs/{created['id']}").json()
    assert fetched["mode"] == "audio"


def test_create_job_accepts_explicit_video_mode() -> None:
    """An explicit ``mode: "video"`` is accepted and persisted on the job."""

    client = TestClient(app)
    created = client.post(
        "/jobs",
        json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "mode": "video",
        },
    ).json()

    assert created["mode"] == "video"

    fetched = client.get(f"/jobs/{created['id']}").json()
    assert fetched["mode"] == "video"


def test_create_job_accepts_explicit_audio_mode() -> None:
    """An explicit ``mode: "audio"`` is accepted and persisted on the job."""

    client = TestClient(app)
    created = client.post(
        "/jobs",
        json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "mode": "audio",
        },
    ).json()

    assert created["mode"] == "audio"


def test_create_job_rejects_unknown_mode_with_422() -> None:
    """Unknown ``mode`` values are rejected with HTTP 422 by Pydantic."""

    client = TestClient(app)
    response = client.post(
        "/jobs",
        json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "mode": "ogg",
        },
    )

    assert response.status_code == 422
    # The validation error body should mention the ``mode`` field.
    errs = response.json().get("detail", [])
    locs = [loc[-1] for loc in (e.get("loc", []) for e in errs)]
    assert "mode" in locs


# ---------------------------------------------------------------------------
# SQLite dual-write persistence tests
# ---------------------------------------------------------------------------

import sqlite3


def _read_job_rows(db_path) -> list[dict]:
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT id, url, mode, status, created_at, updated_at FROM jobs"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        connection.close()


def test_created_job_is_persisted_to_sqlite(tmp_path) -> None:
    """A created job should also be present in the SQLite ``jobs`` table."""

    db_path = tmp_path / "library.db"
    set_jobs_db_path(db_path)
    try:
        client = TestClient(app)
        created = client.post(
            "/jobs",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        ).json()

        rows = _read_job_rows(db_path)
        assert len(rows) == 1
        row = rows[0]
        assert row["id"] == created["id"]
        assert row["url"] == created["url"]
        assert row["mode"] == "audio"
        assert row["status"] == "pending"
        # Both timestamps are ISO-8601 strings.
        assert isinstance(row["created_at"], str) and row["created_at"]
        assert isinstance(row["updated_at"], str) and row["updated_at"]
    finally:
        set_jobs_db_path(database.DEFAULT_DB_PATH)


def test_job_status_update_is_persisted_to_sqlite(tmp_path) -> None:
    """Transitioning a job via ``/complete`` should be reflected in SQLite."""

    db_path = tmp_path / "library.db"
    set_jobs_db_path(db_path)
    try:
        client = TestClient(app)
        created = client.post(
            "/jobs",
            json={"url": "https://youtu.be/abcdefghijk", "mode": "video"},
        ).json()
        job_id = created["id"]

        # created_at captured before transition.
        before = _read_job_rows(db_path)[0]
        original_created = before["created_at"]

        client.post(f"/jobs/{job_id}/complete")

        rows = _read_job_rows(db_path)
        assert len(rows) == 1
        row = rows[0]
        assert row["id"] == job_id
        assert row["mode"] == "video"
        assert row["status"] == "completed"
        # created_at must be preserved on update; updated_at must change.
        assert row["created_at"] == original_created
        assert row["updated_at"] != original_created
    finally:
        set_jobs_db_path(database.DEFAULT_DB_PATH)


def test_job_persistence_swallows_db_error(monkeypatch, tmp_path) -> None:
    """A database failure during ``create_job`` must not break the in-memory store."""

    def boom(*args, **kwargs):
        raise sqlite3.OperationalError("disk full")

    monkeypatch.setattr(jobs_mod, "init_db", boom)
    set_jobs_db_path(tmp_path / "library.db")
    try:
        job = create_job("https://www.youtube.com/watch?v=dQw4w9WgXcQ", mode="audio")
        # In-memory store still holds the job.
        assert job["status"] == "pending"
        assert get_job(job["id"]) is not None
        # No database file was written.
        assert not (tmp_path / "library.db").is_file()
    finally:
        set_jobs_db_path(database.DEFAULT_DB_PATH)


# ---------------------------------------------------------------------------
# DELETE /jobs/{id}
# ---------------------------------------------------------------------------

def test_delete_job_returns_204_and_removes_from_store() -> None:
    """DELETE /jobs/{id} returns 204 and removes the job from the store."""

    client = TestClient(app)
    created = client.post(
        "/jobs",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    ).json()
    job_id = created["id"]

    response = client.delete(f"/jobs/{job_id}")

    assert response.status_code == 204
    # The job is gone from the in-memory store.
    assert client.get(f"/jobs/{job_id}").status_code == 404
    # The list no longer contains it.
    items = client.get("/jobs").json()["items"]
    assert all(item["id"] != job_id for item in items)


def test_delete_job_unknown_id_returns_404() -> None:
    """DELETE /jobs/{id} on an unknown id returns 404 with a clear detail."""

    client = TestClient(app)

    response = client.delete("/jobs/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_delete_job_after_complete_removes_persisted_row(tmp_path) -> None:
    """Deleting a completed job should also remove its SQLite row."""

    db_path = tmp_path / "library.db"
    set_jobs_db_path(db_path)
    try:
        client = TestClient(app)
        created = client.post(
            "/jobs",
            json={"url": "https://youtu.be/abcdefghijk"},
        ).json()
        job_id = created["id"]
        client.post(f"/jobs/{job_id}/complete")

        # Sanity: the row is there before deletion.
        assert len(_read_job_rows(db_path)) == 1

        delete_response = client.delete(f"/jobs/{job_id}")
        assert delete_response.status_code == 204

        # The SQLite row is removed.
        rows = _read_job_rows(db_path)
        assert all(row["id"] != job_id for row in rows)
    finally:
        set_jobs_db_path(database.DEFAULT_DB_PATH)


# ---------------------------------------------------------------------------
# load_jobs_from_db() hydration
# ---------------------------------------------------------------------------

def test_load_jobs_from_db_hydrates_in_memory_store(tmp_path) -> None:
    """A DB-seeded job appears in ``list_jobs()`` with correct fields and
    timestamps after calling :func:`load_jobs_from_db`."""

    from app.jobs import load_jobs_from_db

    db_path = tmp_path / "library.db"
    # Seed the database first via the dual-write path.
    set_jobs_db_path(db_path)
    try:
        client = TestClient(app)
        created = client.post(
            "/jobs",
            json={
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "mode": "audio",
            },
        ).json()
        job_id = created["id"]

        # Capture the persisted timestamps for later comparison.
        persisted = _read_job_rows(db_path)[0]
        created_at = persisted["created_at"]
        updated_at = persisted["updated_at"]

        # Simulate a process restart by clearing the in-memory store.
        reset_jobs()
        assert list_jobs_mod_list() == []

        # Hydrate from the DB.
        loaded = load_jobs_from_db(db_path)
        assert loaded == 1

        # The job reappears with its original fields and timestamps.
        items = list_jobs_mod_list()
        assert len(items) == 1
        job = items[0]
        assert job["id"] == job_id
        assert job["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert job["status"] == "pending"
        assert job["mode"] == "audio"

        # Timestamps side-table is repopulated with the persisted values.
        from app import jobs as jobs_module

        ts = jobs_module._JOB_TIMESTAMPS[job_id]
        assert ts["created_at"] == created_at
        assert ts["updated_at"] == updated_at
    finally:
        set_jobs_db_path(database.DEFAULT_DB_PATH)


def test_load_jobs_from_db_preserves_insertion_order(tmp_path) -> None:
    """Multiple DB-seeded jobs are hydrated in ``created_at`` order, matching
    the original creation order."""

    from app.jobs import load_jobs_from_db

    db_path = tmp_path / "library.db"
    set_jobs_db_path(db_path)
    try:
        client = TestClient(app)
        first = client.post(
            "/jobs", json={"url": "https://youtu.be/aaaaaaaaaaa"}
        ).json()
        second = client.post(
            "/jobs", json={"url": "https://youtu.be/bbbbbbbbbbb"}
        ).json()

        reset_jobs()
        loaded = load_jobs_from_db(db_path)
        assert loaded == 2

        items = list_jobs_mod_list()
        assert [j["id"] for j in items] == [first["id"], second["id"]]
    finally:
        set_jobs_db_path(database.DEFAULT_DB_PATH)


def test_load_jobs_from_db_returns_zero_when_no_table(tmp_path) -> None:
    """Loading from a database file that has no ``jobs`` table is a quiet
    no-op returning 0 (not an error)."""

    from app.jobs import load_jobs_from_db

    db_path = tmp_path / "library.db"
    # Create the file but only the metadata table (no jobs table).
    database.init_db(db_path)
    # Drop the jobs table to simulate a pre-jobs-era database.
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("DROP TABLE IF EXISTS jobs")
        conn.commit()
    finally:
        conn.close()

    loaded = load_jobs_from_db(db_path)
    assert loaded == 0
    assert list_jobs_mod_list() == []


def test_load_jobs_from_db_returns_zero_when_db_missing(tmp_path) -> None:
    """Loading from a non-existent database file returns 0 and leaves the
    in-memory store untouched."""

    from app.jobs import load_jobs_from_db

    missing = tmp_path / "does-not-exist.db"
    loaded = load_jobs_from_db(missing)
    assert loaded == 0


# Convenience wrapper so tests don't have to import the module function each
# time. Kept tiny to avoid touching the existing import block.
def list_jobs_mod_list():
    from app.jobs import list_jobs

    return list_jobs()
