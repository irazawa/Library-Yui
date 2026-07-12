from fastapi.testclient import TestClient

from app.jobs import reset_jobs
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
