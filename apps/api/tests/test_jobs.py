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


def test_get_job_unknown_id_returns_404():
    client = TestClient(app)

    response = client.get("/jobs/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"
