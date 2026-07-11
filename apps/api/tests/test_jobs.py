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
