from fastapi.testclient import TestClient

from app import downloader as downloader_mod
from app.downloader import DOWNLOADS_ENABLED_FLAG
from app.jobs import reset_jobs
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
